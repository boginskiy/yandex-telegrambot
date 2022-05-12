from logging import StreamHandler
from dotenv import load_dotenv
from telegram import Bot
import exceptions as err
import requests
import logging
import time
import sys
import os


LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s'
logging.basicConfig(
    filename='bot_main.log',
    level=logging.DEBUG,
    format=LOG_FORMAT,
    filemode='w',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщений в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except Exception as error:
        logger.error('Ошибка при отправке сообщения')
        raise Exception(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """
    Запрос к эндпоинту API-сервиса. При успешном запросе ответ API.
    преобразовывается в .json().
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(error, exc_info=True)
        raise err.RequestsError(f'Ошибка запроса API: {error}')
    if response.status_code != 200:
        status_code = response.status_code
        logger.error('Ошибка ответа API = response.status_code != 200')
        raise err.ResponseError(f'Ошибка ответа API {status_code}')
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if isinstance(response, dict):
        try:
            homeworks = response.get('homeworks')
        except KeyError:
            logger.error('Ошибка словаря по ключу homeworks')
            raise KeyError('Ошибка словаря по ключу homeworks')
        try:
            homework = homeworks[0]
        except IndexError:
            logger.error('Список домашних работ пуст')
            raise IndexError('Список домашних работ пуст')
        return homework
    else:
        logger.error('Проверить type параметра response = dict')
        raise TypeError('Проверить type параметра response = dict')


def parse_status(homework):
    """Принимает конкретную домашнюю работу homework."""
    if "homework_name" not in homework:
        raise KeyError("homework_name отсутствует в homework")
    try:
        homework_name = homework.get('homework_name')
    except KeyError:
        logger.error('Ошибка ключа "homework_name"')
        raise KeyError('Ошибка ключа "homework_name"')
    try:
        homework_status = homework.get('status')
    except KeyError:
        logger.error('Ошибка ключа "status"')
        raise KeyError('Ошибка ключа "status"')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'Неизвестный статус выполнения работы {homework_name}')
        raise KeyError(
            f'Неизвестный статус выполнения работы {homework_name}'
        )
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Ошибка переменных окружения')
        raise Exception(
            'Ошибка переменных окружения, проверить содержание файла .env'
        )
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    STATUS_HOME_WORK = ''
    STATUS_ERROR_MAIN = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            message = parse_status(homework)  # Возвращение строки ответа
            if message != STATUS_HOME_WORK:
                # print(message)
                send_message(bot, message)
                STATUS_HOME_WORK = message
            else:
                logger.debug('Обновление статуса сообщения раз в 10 минут')
        except Exception as error:
            message = f'Сбой в работе программы главной функции: {error}'
            if message != STATUS_ERROR_MAIN:
                send_message(bot, message)
                STATUS_ERROR_MAIN = message
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
