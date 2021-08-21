import argparse
import logging
import select
import socket
import sys
import json
import time

import logs.conf.server_log_config
from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, MESSAGE_TEXT, \
    MESSAGE, SENDER, MESSAGE_KEY, ACCOUNT_KEY, DESTINATION, RESPONSE_200, RESPONSE_400, EXIT, GETCLIENTS, \
    STATUS, LIST, RESPONSE_CLIENTS, RESPONSE
from common.utils import get_message, send_message, create_arg_parser

LOGGER = logging.getLogger('server')  # забрали  логгер из конфига


class MsgServer:
    def __init__(self):
        self.clients = []
        self.messages = []
        self.names = dict()
        LOGGER.info('Разбираем параметры для запуска сервера')
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        self.listen_address = namespace.a
        self.listen_port = namespace.p

        if not 1023 < self.listen_port < 65535:
            LOGGER.critical(f'Невозможно запустить сервер на порту {self.listen_port}, порт занят или недопустим')
            sys.exit(1)

    def process_client_message(self, message, client):
        """ метод разбирающий клиентские сообщения. Принимает на вход словарь сообщения, проверяет их корректность,
         ничего не возвращает, отравляет ответ клиенту в виде словаря
        """
        LOGGER.debug(f'Попытка разобрать клиентское сообщение: {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # если клиента нет с вписке подключеных то добавляем
            try:
                if message[USER][ACCOUNT_NAME] not in self.names.keys():
                    self.names[str(message[USER][ACCOUNT_NAME])] = client
                    print(f'Подключен клиент {message[USER][ACCOUNT_NAME]}')
                    send_message(client, RESPONSE_200)
                else:
                    response = RESPONSE_400
                    response[ERROR] = 'Имя пользователя уже занято'
                    send_message(client, response)
                    self.clients.remove(client)
                    client.close()
                return
            except Exception as err:
                print(1, err)

        if ACTION in message and message[ACTION] == GETCLIENTS and TIME in message and USER in message:
            # запрашиваем список  подключеных клиентов
            user_list = list(self.names.keys())
            # print(user_list)
            # если клиенты есть добавляем строку в ответ, если нет - возвращаем 204
            if user_list != '':
                RESPONSE_CLIENTS[RESPONSE] = 201
                RESPONSE_CLIENTS[LIST] = user_list
            else:
                RESPONSE_CLIENTS[RESPONSE] = 204
                LOGGER.debug(f'Нет клиентов подключеных к серверу')
            try:
                send_message(client, RESPONSE_CLIENTS)
                LOGGER.debug(f'Отправка списка клиентов подключеных к серверу {user_list}')
                return
            except Exception as err:
                print(1, err)

        # если пришел EXIT:
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            this_one = self.names[message[ACCOUNT_NAME]]
            print(f'Отключен клиент {message[SENDER]}')
            self.clients.remove(this_one)
            this_one.close()
            del this_one
            return
        # если  пришло сообщение
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message[USER] \
                and DESTINATION in message and SENDER in message:
            # print(message)
            LOGGER.debug(f"От клиета {message[SENDER]} получено сообщение {message[USER][MESSAGE_TEXT]}")
            self.messages.append(message)
            # send_message(client, RESPONSE_200)
            return

        # если ничего не подошло:
        else:
            LOGGER.debug(f"Некорректный запрос, вернуть 400")
            response = RESPONSE_400
            response[ERROR] = 'Некорректный запрос'
            send_message(client, response)
            return

    def process_message(self, message, to_send_data_list):
        """
        метод адресной отправки сообщения определённому клиенту, принимает на вход сообщение,
        и слушающие сокеты. Ничего не возвращает.
        Вызывает отправку сообщения нужному клиенту
        """
        # print(self.names[message[DESTINATION]])
        # # print(self.names)
        # print(to_send_data_list)
        # print(message[DESTINATION])
        # print(self.names.keys())

        if message[DESTINATION] in self.names.keys() and self.names[message[DESTINATION]] in to_send_data_list:
            # print(self.names[message[DESTINATION]])
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')

        elif message[DESTINATION] == 'ALL':
            LOGGER.debug(f'Отправляем  сообщение {message} всем клиентам')
            for one_client in to_send_data_list:
                try:
                    send_message(one_client, message)
                    LOGGER.debug(f'Отправлено сообщение {message} клиенту {one_client}')
                except:
                    LOGGER.info(f'{one_client.getpeername()} отключился от сервера')
                    self.clients.remove(one_client)

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in to_send_data_list:
            raise ConnectionError
        else:

            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')
            LOGGER.debug(
                f'на сервере остались {self.names.keys()} ')


    def start(self):
        LOGGER.info('Попытка запуска сервера')
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.bind((self.listen_address, self.listen_port))
            transport.listen(MAX_CONNECTIONS)
            transport.settimeout(0.1)
        except OSError as err:
            LOGGER.error(
                f'Адрес {self.listen_address} и порт {self.listen_port} не  могут быть использованы для запуска,'
                f' потому что уже используются другой программой', err)
            sys.exit(1)
        else:
            print(
                f'Запущен сервер прослушивающий на {self.listen_address if self.listen_address else "любом"} '
                f'ip-адресе и {self.listen_port} порту')
            LOGGER.info(
                f'Запущен сервер прослушивающий на {self.listen_address if self.listen_address else "любом"} ip-адресе'
                f' и {self.listen_port} порту')

        while True:

            # Принимаем подключения
            try:
                client, client_address = transport.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Установлено соединение с адресом {client_address}')
                self.clients.append(client)
            incoming_data_list = []
            to_send_data_list = []
            errors_list = []

            # проверяем есть ли новые клиенты или данные от уже подключеных
            try:
                if self.clients:
                    incoming_data_list, to_send_data_list, errors_list = select.select(self.clients, self.clients, [],
                                                                                       0)
                    # print(incoming_data_list, to_send_data_list, self.clients)
            except OSError:
                pass

            # парсим сообщения слиентов и есть есть сообщения кладем их в словарь сообщений,
            # если ошибка - исключаем клиента
            if incoming_data_list:
                for sended_from_client in incoming_data_list:
                    try:
                        self.process_client_message(get_message(sended_from_client), sended_from_client)
                    except:
                        LOGGER.info(f'{sended_from_client.getpeername()} отключился от сервера')
                        self.clients.remove(sended_from_client)

            # print(self.messages)

            # проверяем есть ли ожидающие сообщений клиенты и сообщения для отправки, и отправляем их клиентам
            # if to_send_data_list and self.messages:
            #     message = {
            #         ACTION: MESSAGE,
            #         TIME: time.time(),
            #         SENDER: self.messages[0][ACCOUNT_KEY],
            #         MESSAGE_TEXT: self.messages[0][MESSAGE_KEY],
            #     }
            #     del self.messages[0]
            #     for one_client in to_send_data_list:
            #         try:
            #             LOGGER.info(f'Отправляем сообщение {message} клиенту {one_client}')
            #             send_message(one_client, message)
            #         except:
            #             LOGGER.info(f'{one_client.getpeername()} отключился от сервера')
            #             self.clients.remove(one_client)

            for one_message in self.messages:
                try:
                    LOGGER.debug(f'Обработка сообщения {one_message}')
                    self.process_message(one_message,to_send_data_list)
                except Exception:
                    LOGGER.info(f'Соединение с {one_message[DESTINATION]} разорвано')
                    self.clients.remove(self.names[one_message[DESTINATION]])
                    del self.names[one_message[DESTINATION]]
            self.messages.clear()




if __name__ == '__main__':
    server = MsgServer()
    server.start()
