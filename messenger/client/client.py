"""Программа-клиент"""
import logging
import os
import sys
import json
import socket
import threading
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
import_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.append(import_path)
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE_TEXT, MESSAGE, EXIT, SENDER, DESTINATION, RESPONSE_200, GETCLIENTS, LIST, RESPONSE_204, \
    GETCONTACTS, ADD_CONTACT, REMOVE_CONTACT
from common.utils import get_message, send_message, create_arg_parser
import common.errors as errors
from common.decor import func_log
from common.errors import IncorrectDataReceivedError, ReqFieldMissingError, ServerError
from common.metaclasses import ClientVerifier
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from client_database import ClientStorage

LOGGER = logging.getLogger('client')  # забрали логгер из конфига




class MsgClient(threading.Thread, metaclass=ClientVerifier):
    # Объект блокировки сокета и работы с базой данных
    
    def __init__(self):
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079 -m send/listen
        self.remote_users = []
        self.client_name = ''
        self.get_start_params()
        self.get_connect()
        self.database = ''
        self.sock_lock = threading.Lock()
        self.database_lock = threading.Lock()
        super(MsgClient, self).__init__()

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
        # dir_path = os.path.dirname(os.path.realpath(__file__))
        name = self.client_name
        while True:
            if answer == '400 : Имя пользователя уже занято':
                LOGGER.error('400 : Имя пользователя уже занято')
                name = input(
                    'Это имя занято. Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            elif answer == RESPONSE_200:
                break
            elif name == '':
                name = input('Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            answer = self.hello(name)  # 2 todo 'если при первом вводе имени выбрать занятое то потом нельзя зайти'
        print(f'Вы видны всем под именем {self.client_name}')
        db_name_path = os.path.join('db', f'{self.client_name}.db3')
        self.database = ClientStorage(db_name_path)  # инициализируем db

        self.database_load()
        self.start_threads()
        # self.get_destination()  # 4

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

    # функция текстовое меню
    # def get_destination(self):
    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        self.print_help()
        while True:
            command = input('Введите команду:\n ')
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
                LOGGER.debug('Запрошен список активных пользователей с cервера')
                # with self.sock_lock:
                self.get_clients()
                with self.database_lock:
                    self.database.add_users(self.remote_users)
                print(self.remote_users)

            # Список контактов
            elif command == 'contacts':
                with self.database_lock:
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
            with self.database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                    try:
                        with self.sock_lock:
                            self.remove_contact(edit)
                    except ServerError:
                        LOGGER.error('Не удалось отправить информацию на сервер.')
                else:
                    LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with self.database_lock:
                    self.database.add_contact(edit)
                # with self.sock_lock:
                try:
                    with self.sock_lock:
                        self.add_contact(edit)
                except ServerError:
                    LOGGER.error('Не удалось отправить информацию на сервер.')
            else:
                print('Нет такого пользователя')

    # Функция выводящая справку по использованию.
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
        # with self.sock_lock:
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
        with self.database_lock:
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
        # with self.database_lock:
        self.database.write_log('me', destination, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        # with self.sock_lock:
        try:
            send_message(self.transport, out)
            LOGGER.info(f'Отправлено сообщение для пользователя {destination}')
        except OSError as err:
            if err.errno:
                LOGGER.critical('Потеряно соединение с сервером.')
                exit(1)
            else:
                LOGGER.error('Не удалось передать сообщение. Таймаут соединения')
        else:
            return

    def process_ans(self, message):
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return RESPONSE_200
            elif message[RESPONSE] == 204:
                return RESPONSE_204
            # elif message[RESPONSE] == 201:
            #     LOGGER.debug(f'process_ans Получен ответ  - список пользователей сервера {message[LIST]}')
            #     self.remote_users = [x for x in message[LIST] if x != str(self.client_name)]
            #     print(self.remote_users)
            #     self.get_destination()
            # elif message[RESPONSE] == 202:
            #     LOGGER.debug(f'Получен ответ - список контактов {message[LIST]}')
            #     for contact in message[LIST]:
            #         self.database.add_contact(contact)
            else:
                raise ServerError('Ошибка связи с сервером')
            #     return
        else:
            return f'400 : {message[ERROR]}'
        raise errors.ReqFieldMissingError(RESPONSE)

    def client_receiving(self):
        LOGGER.debug('Запуск потока получения')
        LOGGER.info('Режим работы - прием сообщений')
        while True:
            time.sleep(1)
            with self.sock_lock:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            # time.sleep(1)
                try:
                    self.transport.settimeout(1)
                    message = get_message(self.transport)
                    LOGGER.debug(f'что-то пришло')
                # Проблемы с соединением
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                    sys.exit(1)
                    # Принято некорректное сообщение
                except IncorrectDataReceivedError:
                    LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION \
                            in message and MESSAGE_TEXT in message[USER] and message[DESTINATION] == self.client_name:
                        print(f'\nUser {message[SENDER]} sent: {message[USER][MESSAGE_TEXT]}')
                        LOGGER.info(f'Сообщение из чята от {message[SENDER]}: {message[USER][MESSAGE_TEXT]}')
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                        with self.database_lock:
                            try:
                                self.database.write_log(message[SENDER], self.client_name, message[MESSAGE_TEXT])
                            except:
                                LOGGER.error('Ошибка взаимодействия с базой данных')
                self.transport.settimeout(5)


    # Функция запроса списка активных пользователей
    def get_clients(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.client_name}')
        request = self.create_presence(self.client_name)
        request[ACTION] = GETCLIENTS
        with self.sock_lock:
            send_message(self.transport, request)
            ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 201:
            LOGGER.debug(f'getclients Получен ответ  - список пользователей сервера {ans[LIST]}')
            self.remote_users = [x for x in ans[LIST] if x != str(self.client_name)]
        # else:
        #     self.print_user_message(ans)

        #     self.remote_users = [x for x in ans[LIST] if x != str(self.client_name)]
        # return
        # else:
        #     raise ServerError

    # Функция запроса списка контактов
    def contacts_list_request(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.client_name}')
        req = {
            ACTION: GETCONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        # with self.sock_lock:
        send_message(self.transport, req)
        ans = get_message(self.transport)
        #     LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
        #     self.process_ans(ans)
        # else:
        #     self.print_user_message(ans)
            for contact in ans[LIST]:
                self.database.add_contact(contact)
        return
        # else:
        #     raise ServerError
        # return

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
        return

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
        print('Удачное удаление контакта.')
        return

        # Функция выводящяя историю сообщений

    def print_history(self):
        ask = input('Показать историю переписки с (имя контакта): ')
        with self.database_lock:
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


    def start_threads(self):
        LOGGER.debug('Запуск потока получения')
        receive_thread = threading.Thread(target=self.client_receiving, daemon=True)
        send_thread = threading.Thread(target=self.client_sending, daemon=True)
        receive_thread.start()
        send_thread.start()
        receive_thread.join()
        send_thread.join()
        LOGGER.debug('Потоки запущены')
        return


def main():
    client = MsgClient()
    # client.daemon = True
    # client.start()
    client.hello_user()


if __name__ == '__main__':
    main()
