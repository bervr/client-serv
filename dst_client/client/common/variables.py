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


# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'destination'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'


# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
GETCLIENTS = 'getclients'
GETCONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
REMOVE_CONTACT = 'remove_contact'
USERS_REQUEST = 'get_users'
MESSAGE_TEXT = 'message_text'
MESSAGE_KEY = 1
ACCOUNT_KEY = 0
EXIT = 'exit'
STATUS = 'status_message'
LIST = 'user_list'
MYCOLOR = '0900FF'
NOTMYCOLOR = '000000'
PUBLIC_KEY_REQUEST = 'get_public_key'

# Словари - ответы:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
RESPONSE_204 = {RESPONSE: 204}
RESPONSE_202 = {RESPONSE: 202}
RESPONSE_205 = {RESPONSE: 205}
RESPONSE_CLIENTS = {
    RESPONSE: 201
}
RESPONSE_511 = {
    RESPONSE: 511,
    DATA: None
}
