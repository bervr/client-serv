"""Константы"""

# Порт по умолчанию для сетевого взаимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 4096
# Кодировка проекта
ENCODING = 'utf-8'
# Уровень логирования
# LOGGING_LEVEL = 'INFO'
LOGGING_LEVEL = 'DEBUG'
SERVER_DATABASE = 'sqlite:///srv_msg_db.db3'
CLIENT_DATABASE = 'sqlite:///cln_msg_db.db3'


# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'destination'


# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
GETCLIENTS = 'getclients'
MESSAGE_TEXT = 'message_text'
MESSAGE_KEY = 1
ACCOUNT_KEY = 0
EXIT = 'exit'
STATUS = 'status_message'
LIST = 'user_list'
MYCOLOR = '0900FF'
NOTMYCOLOR = '000000'

# Словари - ответы:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
RESPONSE_204 = {RESPONSE: 204}
RESPONSE_CLIENTS = {
    RESPONSE: 201
}
