import os
import sys
import time
import requests
from http import HTTPStatus
import logging
from logging import StreamHandler
from dotenv import load_dotenv
from telegram import Bot
import exceptions as err


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
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s'


def send_message(bot, message):
    """Отправка сообщений в Telegram чат."""
    try:
        logger.info('Отправка нового сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise Exception(f'Ошибка при отправке сообщения: {error}')
    else:
        logger.info('Сообщение успешно отправлено')


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
        raise err.RequestsError(f'Ошибка запроса API: {error}')
    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code
        raise err.ResponseError(
            f'Ошибка ответа API {status_code} != {HTTPStatus.OK}'
        )
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Проверить type параметра response -> dict')
    homeworks = response.get('homeworks')
    if not homeworks:
        raise Exception('Список домашних работ пуст')
    elif type(homeworks) != list:
        raise Exception('Проверить параметр "homeworks" -> list')
    homework = homeworks[0]
    return homework


def parse_status(homework):
    """Принимает конкретную домашнюю работу homework."""
    if 'homework_name' not in homework:
        raise KeyError('ключ "homework_name" отсутствует в homework')
    elif 'status' not in homework:
        raise KeyError('ключ "status" отсутствует в homework')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(
            f'Неизвестный статус выполнения работы {homework_name}'
        )
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
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
            message = parse_status(homework)
            if message != STATUS_HOME_WORK:
                send_message(bot, message)
                STATUS_HOME_WORK = message
            else:
                logger.debug('Обновление статуса сообщения раз в 10 минут')
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы главной функции: {error}'
            if message != STATUS_ERROR_MAIN:
                send_message(bot, message)
                STATUS_ERROR_MAIN = message
            time.sleep(RETRY_TIME)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
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
    main()
