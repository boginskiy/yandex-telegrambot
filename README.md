# Телеграмм бот «yandex-telegrambot»

### Описание
Бот осуществляет проверку статуса отправленных данных путем опроса API сервиса Яндекс, анализирует ответ и отправляет соответствующее уведомление пользователю, при этом ведется логирование процессов с сообщением о проблемах.

### Технологии
* Python 3.7
* python-dotenv 0.19.0
* python-telegram-bot 13.7
* requests==2.26.0

### Запуск проекта на Linux
Клонировать проект c GitHub
```
git clone git@github.com:boginskiy/yandex-telegrambot.git
```
Установить виртуальное окружение venv
```
python3 -m venv venv
```
Активировать виртуальное окружение venv
```
source venv/bin/activate
```
Обновить менеджер пакетов pip
```
python3 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
Запуск
```
python3 homework.py
```

### **Автор**
[Богинский Дмитрий](https://github.com/boginskiy) - python разработчик
