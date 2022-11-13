import argparse
import logging
import socket
import sys
import json
import logs.conf.server_log_config
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT
from common.utils import get_message, send_message, create_arg_parser


SERVER_LOGGER = logging.getLogger('server')  # забрали  логгер из конфига



class MsgServer:
    def process_client_message(self, message):
        SERVER_LOGGER.debug(f'Попытка разобрать клиентское сообщение: {message}')
        try:
            if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message \
                    and message[USER][ACCOUNT_NAME] == 'Guest':
                return {RESPONSE: 200}
            return {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
        except Exception:
            print('Некорретный формат сообщения')



    def start(self):
        SERVER_LOGGER.info('Попытка запуска сервера')
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        listen_address = namespace.a
        listen_port = namespace.p

        if not 1023 < listen_port < 65535:
            SERVER_LOGGER.critical(f'Невозможно запустить сервер на порту {listen_port}, порт занят или недопустим')
            sys.exit(1)

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.listen(MAX_CONNECTIONS)
        SERVER_LOGGER.info(f'Запущен сервер прослушивающий на {listen_address if listen_address else "любом"} ip-адресе'
                           f' и {listen_port} порту')

        while True:
            client, client_address = transport.accept()
            SERVER_LOGGER.info(f'Установлено соединение с адресом {client_address}')
            try:
                message_from_client = get_message(client)
                SERVER_LOGGER.debug(f'Получено соощение {message_from_client}')
                print(message_from_client)
                response = self.process_client_message(message_from_client)
                SERVER_LOGGER.info(f'Сформирован ответ {response}')
                send_message(client, response)
                SERVER_LOGGER.debug(f'Закрывается соединение с слиентом {client_address}')
                client.close()
            except (ValueError, json.JSONDecodeError):
                # print('Принято некорретное сообщение от клиента.')
                SERVER_LOGGER.error(f'Не удалось декодировать JSON от клиента  {client_address}, соедиение закрывается')
                client.close()


if __name__ == '__main__':
    server = MsgServer()
    server.start()
