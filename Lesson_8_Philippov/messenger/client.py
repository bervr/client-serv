"""Программа-клиент"""
import logging
import sys
import json
import socket
import time
import argparse
import logs.conf.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE_TEXT, MESSAGE, EXIT, SENDER, DESTINATION, RESPONSE_200, GETCLIENTS, LIST, RESPONSE_204
from common.utils import get_message, send_message, create_arg_parser
import common.errors as errors
from decor import func_log
from threading import Thread

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class MsgClient:
    @func_log
    def create_presence(self, account_name='Guest'):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        LOGGER.debug(f'Сформирован presence: {out}')
        return out

    @func_log
    def add_client_name(self, name):
        if name != '':
            self.client_name = name
            LOGGER.info(f'установлено имя {self.client_name}')
        else:
            self.client_name = self.transport.getsockname()[1]

        # print(self.client_name)
        return self.client_name

    def hello_user(self, answer=None):
        while answer != RESPONSE_200:
            if answer == '400 : Имя пользователя уже занято':
                LOGGER.error('400 : Имя пользователя уже занято')
                print('400 : Имя пользователя уже занято')
            # self.client_name = ''
            user_name = input('Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            # if user_name == '???':
            #     self.get_clients()
            #     answer = None
            #     continue
            answer = self.hello(user_name)  # todo 'если при первом вводе имени выбрать занятое то потом нельзя зайти анонимно'
            # print(answer)
        print(f'Вы видны всем под именем {self.client_name}')

    def hello(self, user_name):
        # print('start ', self.client_name)
        self.add_client_name(user_name)
        # print('stop ', self.client_name)
        message_to_server = self.create_presence(self.client_name)
        # print(message_to_server)
        send_message(self.transport, message_to_server)
        LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
        try:
            answer = self.process_ans(get_message(self.transport))
            LOGGER.info(f'Получен ответ от сервера {answer}')
        except (ValueError, json.JSONDecodeError):
            print('Не удалось декодировать сообщение сервера.')
            LOGGER.critical(f'Не удалось декодировать сообщение от сервера')
            return
        else:
            return answer



    def get_destination(self):
        while True:
            new_dst = input('??? чтобы запросить список клиентов.\n'
                            '!!! для выхода\n'
                            'Кому вы хотите отправить сообщение? Нажмите Enter если всем\n')
            if new_dst == '???':
                self.get_clients()
                self.process_ans(get_message(self.transport))
                print(self.remote_users)
                continue
            elif new_dst == '!!!':
                self.user_exit()
            elif new_dst == '':
                new_dst = 'ALL'
            return new_dst

    def user_exit(self):
        self.create_exit_message(self.client_name)
        self.transport.close()
        LOGGER.info('Пользователь завершил работу приложения')
        sys.exit(0)

    def create_message(self, destination, account_name='Guest'):
        message = input('Введите сообщение для отправки или !!! для выхода:\n')
        if message == '!!!':
            self.user_exit()
        out = {
            DESTINATION: destination,
            SENDER: account_name,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name,
                MESSAGE_TEXT: message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {out}')
        return out

    def process_ans(self, message):
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return RESPONSE_200
            elif message[RESPONSE] == 201:
                # print(self.client_name, type(self.client_name))

                # убираем из ответного списка себя
                self.remote_users = [x for x in message[LIST] if x != str(self.client_name)]
                # self.remote_users = message[LIST]
                print(self.remote_users)
                return
            elif message[RESPONSE] == 204:
                return RESPONSE_204

            return f'400 : {message[ERROR]}'
        raise errors.ReqFieldMissingError(RESPONSE)

    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        while True:
            try:
                send_message(self.transport, self.create_message(self.get_destination(), self.client_name))
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def client_receiving(self):
        LOGGER.info('Режим работы - прием сообщений')
        while True:
            try:
                answer = get_message(self.transport)
                # print(answer)
                if RESPONSE in answer:
                    self.process_ans(answer)
                    # print(self.remote_users)
                else:
                    print(f'\nUser {answer[SENDER]} sent: {answer[USER][MESSAGE_TEXT]}')
                    LOGGER.info(f'Сообщение из чята от {answer[SENDER]}: {answer[USER][MESSAGE_TEXT]}')
                    # print(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def get_clients(self):
        request = self.create_presence(self.client_name)
        request[ACTION] = GETCLIENTS
        # print(request)
        send_message(self.transport, request)
        LOGGER.info(f'Отправка сообщения на сервер - {request}')

    @func_log
    def create_exit_message(account_name):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    def get_start_params(self):
        LOGGER.debug("Попытка получить параметры запуска клиента")
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])

        self.server_address = namespace.a
        self.server_port = namespace.p

        client_mode = namespace.m
        LOGGER.debug(f'Адрес и порт сервера {self.server_address}:{self.server_port}')

    def get_connect(self):
        try:
            self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport.connect((self.server_address, self.server_port))
            # print(f'User{self.transport.getsockname()[1]}')

            LOGGER.debug(
                f'Подключение к серверу с адресом {self.server_address if self.server_address else "localhost"} '
                f'по {self.server_port} порту')
        except ConnectionRefusedError:
            LOGGER.error(f'Не удалось подключится к серверу {self.server_address}:{self.server_port}, '
                         f'возможно он не запущен или что-то с сетью')
        except json.JSONDecodeError:
            LOGGER.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except errors.ServerError as error:
            LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        except errors.ReqFieldMissingError as missing_error:
            LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)

    def __init__(self):
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079 -m send/listen
        self.remote_users = []
        self.client_name = ''
        self.get_start_params()
        self.get_connect()

    def start(self):
        self.hello_user()
        self.start_threads()

    def start_threads(self):
        receive_thread = Thread(target=self.client_receiving, daemon=True)
        send_thread = Thread(target=self.client_sending, daemon=True)
        receive_thread.start()
        send_thread.start()
        receive_thread.join()
        send_thread.join()


if __name__ == '__main__':
    client = MsgClient()
    client.start()
