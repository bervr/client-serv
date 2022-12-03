import os
import socket
import sys
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication

# from common.utils import send_message, get_message

sys.path.append('..')
from common.utils import *
from common.utils import send_message, get_message
from common.variables import *
from common.errors import ServerError, IncorrectDataReceivedError
from client_database import ClientStorage
from main_window import ClientMainWindow
from start_dialog import UserNameDialog

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


# Класс - Транспорт, отвечает за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    # атрибуты класса становятся экземпляры pyqtsignal
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self):
        # вызываем конструкторы предков.
        threading.Thread.__init__(self)
        QObject.__init__(self)
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079 -m send/listen
        self.remote_users = []
        self.username = ''
        self.get_start_params()
        self.get_connect()
        self.database = ''
        self.sock_lock = threading.Lock()
        self.database_lock = threading.Lock()
        self.running = True
        # Сигналы новое сообщение и потеря соединения

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


    def gui_hello(self):
        self.client_app = QApplication(sys.argv)
        # Если имя пользователя не было указано в командной строке, то запросим его
        if not self.username or self.username == '':
            start_dialog = UserNameDialog()
            self.client_app.exec_()
            # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, иначе задаем имя по сокету
            if start_dialog.ok_pressed:
                self.username = start_dialog.client_name.text()
            else:
                self.username = self.transport.getsockname()[1]
                # exit(0)
            del start_dialog
            # LOGGER.debug(f'попытка установить имя {self.username}')
            LOGGER.info(f'установлено имя {self.username}')
            message_to_server = self.create_presence(self.username)
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
                if answer == RESPONSE_200:
                    LOGGER.info(f'Установлено подключение к серверу')
                    db_name_path = os.path.join(f'{self.username}.db3')
                    self.database = ClientStorage(db_name_path)  # инициализируем db
                    self.database_load()
                    self.start_threads()
                    return


    # функция текстовое меню
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



    def transport_shutdown(self):
            self.running = False
            try:
                send_message(self.transport, self.create_exit_message())
            except OSError:
                pass
            LOGGER.debug('Транспорт завершает работу.')
            time.sleep(0.5)

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
            SENDER: self.username,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username,
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
            else:
                raise ServerError('Ошибка связи с сервером')
            #     return
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION \
                in message and MESSAGE_TEXT in message[USER] and message[DESTINATION] == self.username:
            LOGGER.info(f'Сообщение из чята от {message[SENDER]}: {message[USER][MESSAGE_TEXT]}')
            self.new_message.emit(message[SENDER])
            # print(f'\nUser {message[SENDER]} sent: {message[USER][MESSAGE_TEXT]}')
            # Если пакет корретно получен выводим в консоль и записываем в базу.
            with self.database_lock:
                try:
                    self.database.write_log(message[SENDER], self.account_name, message[MESSAGE_TEXT])
                except:
                    LOGGER.error('Ошибка взаимодействия с базой данных')
        else:
            return f'400 : {message[ERROR]}'
        raise errors.ReqFieldMissingError(RESPONSE)

    def client_receiving(self):
        LOGGER.debug('Запуск потока получения')
        LOGGER.info('Режим работы - прием сообщений')

        while self.running:
            time.sleep(1)
            with self.sock_lock:
                # Отдыхаем секунду и снова пробуем захватить сокет.
                # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
                # time.sleep(1)
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                    LOGGER.debug(f'что-то пришло')
                    # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOGGER.debug(f'Соединение с сервером {self.server_address} было утеряно')
                    self.running = False
                    self.connection_lost.emit()
                    # Принято некорректное сообщение
                except IncorrectDataReceivedError:
                    LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                        # break
                else:
                    LOGGER.debug(f'Принято сообщение с сервера: {message}')
                    self.process_ans(message)
                finally:
                    self.transport.settimeout(5)

    # Функция запроса списка активных пользователей
    def get_clients(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        request = self.create_presence(self.username)
        request[ACTION] = GETCLIENTS
        with self.sock_lock:
            send_message(self.transport, request)
            ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 201:
            LOGGER.debug(f'getclients Получен ответ  - список пользователей сервера {ans[LIST]}')
            self.remote_users = [x for x in ans[LIST] if x != str(self.username)]
            LOGGER.debug('Получен список активных пользователей с сервера.')

    # Функция запроса списка контактов
    def contacts_list_request(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.username}')
        req = {
            ACTION: GETCONTACTS,
            TIME: time.time(),
            USER: self.username
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
            LOGGER.debug('Получен список контактов с сервера.')
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
            USER: self.username,
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
            USER: self.username,
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

    # def print_history(self):
    #     ask = input('Показать историю переписки с (имя контакта): ')
    #     with self.database_lock:
    #         history_list = self.database.get_history(ask)
    #         for message in history_list:
    #             print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')

    @func_log
    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
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
        self.username = namespace.n

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
        # send_thread = threading.Thread(target=self.client_sending, daemon=True)
        receive_thread.start()
        main_window = ClientMainWindow(self.database, self.transport)
        main_window.make_connection(self)
        main_window.setWindowTitle(f'Чат Программа alpha release - {self.username}')
        self.client_app.exec_()
        # Раз графическая оболочка закрылась, закрываем транспорт
        self.transport_shutdown()
        # send_thread.start()
        receive_thread.join()
        # send_thread.join()
        LOGGER.debug('Потоки запущены')
        return


def main():
    client = ClientTransport()
    client.gui_hello()
    # client.daemon = True
    # client.start()
    # client.hello_user()


if __name__ == '__main__':
    main()
