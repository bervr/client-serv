"""Программа-клиент"""
import logging
import sys
import json
import socket
import time
import argparse
import logs.conf.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE_TEXT, MESSAGE, EXIT, SENDER, DESTINATION, RESPONSE_200, GETCLIENTS, LIST, RESPONSE_204, \
    GETCONTACTS, ADD_CONTACT, REMOVE_CONTACT
from common.utils import get_message, send_message, create_arg_parser
import common.errors as errors
from decor import func_log
from common.errors import IncorrectDataReceivedError, ReqFieldMissingError, ServerError
from threading import Thread, Lock
from metaclasses import ClientVerifier
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from client_database import ClientStorage

LOGGER = logging.getLogger('client')  # забрали логгер из конфига

# Объект блокировки сокета и работы с базой данных
sock_lock = Lock()
database_lock = Lock()

class MsgClient(metaclass=ClientVerifier):
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # проверка метакласса
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
        else:
            self.client_name = self.transport.getsockname()[1]
        LOGGER.info(f'установлено имя {self.client_name}')
        return self.client_name

    def hello_user(self, answer=None):  # 1
        name = self.client_name
        while True:
            if answer == '400 : Имя пользователя уже занято':
                LOGGER.error('400 : Имя пользователя уже занято')
                # print('400 : Имя пользователя уже занято')
                name = input('Это имя занято. Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            elif answer == RESPONSE_200:
                break
            elif name == '':
                name = input('Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            answer = self.hello(name)  #  2 todo 'если при первом вводе имени выбрать занятое то потом нельзя зайти'
        print(f'Вы видны всем под именем {self.client_name}')
        self.database = ClientStorage(self.client_name)  # инициализируем db
        self.database_load()
        self.get_destination()  # 4

    def hello(self, user_name=''):  # 2
        self.add_client_name(user_name)  # 3
        message_to_server = self.create_presence(self.client_name)
        send_message(self.transport, message_to_server)
        LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
        try:
            answer = self.process_ans(get_message(self.transport))
            LOGGER.debug(f'Получен ответ от сервера {answer}')

        except (ValueError, json.JSONDecodeError):
            print('Не удалось декодировать сообщение сервера.')
            LOGGER.critical(f'Не удалось декодировать сообщение от сервера')
            return
        else:
            return answer

    #функция текстовое меню
    def get_destination(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            # Если отправка сообщения - соответствующий метод
            if command == 'message':
                self.create_message()

            # Вывод помощи
            elif command == 'help':
                self.print_help()

            # Выход. Отправляем сообщение серверу о выходе.
            elif command == 'exit':
                self.user_exit()

            # Список пользователей.
            elif command == 'active':
                LOGGER.debug('Запрошен вывод списка активных пользователей')
                print(self.remote_users)

            # обновить список пользователей с сервера.
            elif command == 'renew':
                LOGGER.debug('Запрошен список активных пользователей с вервера')
                self.get_clients()
                self.database.add_users(self.remote_users)
                print(self.remote_users)

            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_user_contacts()
                for contact in contacts_list:
                    print(contact)

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            # история сообщений.
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

        # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                    try:
                        self.remove_contact(edit)
                    except ServerError:
                        LOGGER.error('Не удалось отправить информацию на сервер.')
                else:
                    LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.add_contact(edit)
                    except ServerError:
                        LOGGER.error('Не удалось отправить информацию на сервер.')
            else:
                print('Нет такого пользователя')

    # Функция выводящяя справку по использованию.
    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('active - показать пользователей на сервере.')
        print('renew - запросить пользователей на сервере.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def user_exit(self):
        # with sock_lock:
        try:
            send_message(self.transport, self.create_exit_message())
            LOGGER.info(f'Отправлено сообщение о завершении сеанса на сервер')
        except:
            pass
        print('Завершение соединения.')
        LOGGER.info('Завершение работы по команде пользователя.')
        # Задержка необходима, чтобы успело уйти сообщение о выходе
        time.sleep(0.5)
        self.transport.close()
        sys.exit(0)

    def create_message(self):
        destination = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(destination):
                LOGGER.error(f'Попытка отправить сообщение незарегистрированному получателю: {destination}')
                return

        # if message == '!!!':
        #     self.user_exit()
        out = {
            DESTINATION: destination,
            SENDER: self.client_name,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name,
                MESSAGE_TEXT: message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {out}')
        # Сохраняем сообщения для истории
        with database_lock:
            self.database.write_log('me', destination, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        # with sock_lock:
        try:
            send_message(self.transport, out)
            LOGGER.info(f'Отправлено сообщение для пользователя {destination}')
        except OSError as err:
            if err.errno:
                LOGGER.critical('Потеряно соединение с сервером.')
                exit(1)
            else:
                LOGGER.error('Не удалось передать сообщение. Таймаут соединения')

    def process_ans(self, message):
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return RESPONSE_200
            elif message[RESPONSE] == 204:
                return RESPONSE_204

            return f'400 : {message[ERROR]}'
        raise errors.ReqFieldMissingError(RESPONSE)

    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        while True:
            try:
                send_message(self.transport, self.create_message())
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def client_receiving(self):
        LOGGER.info('Режим работы - прием сообщений')
        while True:
            try:
                answer = get_message(self.transport)
                if RESPONSE in answer:
                    self.process_ans(answer)
                # elif :
                #     pass
                else:
                    print(f'\nUser {answer[SENDER]} sent: {answer[USER][MESSAGE_TEXT]}')
                    LOGGER.info(f'Сообщение из чята от {answer[SENDER]}: {answer[USER][MESSAGE_TEXT]}')
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    # Функция запроса списка активных пользователей
    def get_clients(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.client_name}')
        request = self.create_presence(self.client_name)
        request[ACTION] = GETCLIENTS
        send_message(self.transport, request)
        ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 201:
            self.remote_users = [x for x in ans[LIST] if x != str(self.client_name)]
            return
        else:
            raise ServerError

    # Функция запроса списка контактов
    def contacts_list_request(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.client_name}')
        req = {
            ACTION: GETCONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        send_message(self.transport, req)
        ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST]:
                self.database.add_contact(contact)
            return
        else:
            raise ServerError
        return


    # Функция добавления пользователя в контакт лист
    def add_contact(self, contact):
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        send_message(self.transport, req)
        ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка создания контакта')
        print('Удачное создание контакта.')

    # Функция удаления пользователя из контакт-листа
    def remove_contact(self, contact):
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        send_message(self.transport, req)
        ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка удаления клиента')
        print('Удачное удаление')

        # Функция выводящяя историю сообщений
    def print_history(self):
        ask = input('Показать историю переписки с (имя контакта): ')
        with database_lock:
            history_list = self.database.get_history(ask)
            for message in history_list:
                print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')

    @func_log
    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }

    def database_load(self):
        # Загружаем список активных пользователей
        try:
            self.get_clients()
        except ServerError:
            LOGGER.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(self.remote_users)
        # Загружаем список контактов
        try:
            print('получаем список контактов с сервера')
            self.contacts_list_request()
            print(' получили список контактов с сервера')
        except ServerError:
            LOGGER.error('Ошибка запроса списка контактов.')
        else:
            return
        # else:
        #     # print(contacts_list)
        #     for contact in contacts_list:
        #         self.database.add_contact(contact)

    def get_start_params(self):
        LOGGER.debug("Попытка получить параметры запуска клиента")
        parser = create_arg_parser(DEFAULT_PORT, DEFAULT_IP_ADDRESS)
        namespace = parser.parse_args(sys.argv[1:])

        self.server_address = namespace.a
        self.server_port = namespace.p
        self.client_name = namespace.n

        client_mode = namespace.m
        LOGGER.debug(f'Адрес и порт сервера {self.server_address}:{self.server_port}')

    def get_connect(self):
        try:
            self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # проверка метакласса
            self.transport.connect((self.server_address, self.server_port))
            # self.transport.listen (1) # проверка метакласса

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
        self.database = ''
        super().__init__()

    def start(self):
        self.hello_user()  # # 1
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
