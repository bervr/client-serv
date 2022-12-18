import os
import socket
import sys
import time
import logging
import json
import threading
import hmac
import binascii
import hashlib

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from Cryptodome.PublicKey import RSA

dir_path = os.path.dirname(os.path.realpath(__file__))
import_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.append(import_path)
from common.decor import func_log
from common.utils import *
from common.utils import send_message, get_message
from common.variables import *
from common.errors import ServerError, IncorrectDataReceivedError, ReqFieldMissingError
from .client_database import ClientStorage
from .main_window import ClientMainWindow
from .start_dialog import UserNameDialog

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class ClientTransport(threading.Thread, QObject):
    """Основной класс клиента, отвечает за взаимодействие с сервером и все остальные вызовы"""
    # Сигналы новое сообщение и потеря соединения
    # атрибуты класса становятся экземпляры pyqtsignal
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()
    message_205 = pyqtSignal()

    def __init__(self):
        # вызываем конструкторы предков.
        threading.Thread.__init__(self)
        QObject.__init__(self)
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079 -m send/listen
        self.remote_users = []
        self.username = None
        self.password = None
        self.keys = ''
        self.get_start_params()
        self.get_connect()
        self.database = ''
        self.sock_lock = threading.Lock()
        self.database_lock = threading.Lock()
        self.running = True
        # Сигналы новое сообщение и потеря соединения

    def create_presence(self, account_name='Guest'):
        """Метод формирования приветственного сообщения"""
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
        """
        Запускающий метод, проверяет стартовые параметры, запраивает логопас если их нет,
        запускает аутентификацию, инициализирует базу данных,
        создает ключи и стартует потоки обмена сообщениями с сервером
        """
        self.client_app = QApplication(sys.argv)
        # Если имя пользователя и пароль не были указаны в командной строке, то запросим их
        if not self.username or not self.password:
            start_dialog = UserNameDialog()
            self.client_app.exec_()
            # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, иначе задаем имя по сокету
            if start_dialog.ok_pressed:
                self.username = start_dialog.client_name.text()
                self.password = start_dialog.client_passwd.text()
                LOGGER.debug(f'Получено имя = {self.username}, пароль = {self.password}.')
            else:
                exit(0)
            del start_dialog
        LOGGER.info(f'установлено имя {self.username}')
        self.load_keys()  # загрузили ключи
        # запускаем аутентификацию

        passwd_bytes = self.password.encode('utf-8')  # Получаем хэш пароля
        salt = self.username.lower().encode('utf-8')  # делаем соль
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)  # получили тоже что лежит на сервере

        LOGGER.debug(f'Passwd hash ready: {passwd_hash_string}')

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        # Авторизируемся на сервере
        with self.sock_lock:
            presense = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey
                }
            }
            LOGGER.debug(f"Отправка сообщения на сервер, пресенс = {presense}")
            # Отправляем серверу приветственное сообщение.
            try:
                send_message(self.transport, presense)
                ans = get_message(self.transport)
                LOGGER.debug(f'Сервер вернул = {ans}.')
                # Если сервер вернул ошибку, бросаем исключение.
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans[DATA]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')  # хешируем соленый
                        # пароль с ответом от сервера
                        digest = hash.digest()  # преобразуем в дайджест
                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(
                            digest).decode('ascii')  # запихиваем в словарь 511 и шлем на сервер
                        LOGGER.debug(f"Отправляем на сервер подтверждение - {my_ans}")
                        send_message(self.transport, my_ans)
                        answer = self.process_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                LOGGER.critical(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')
            except (ValueError, json.JSONDecodeError) as err:
                LOGGER.critical(f'Не удалось декодировать сообщение от сервера', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')
            else:
                if answer == RESPONSE_200:
                    LOGGER.info(f'Установлено подключение к серверу')
                    db_name_path = os.path.join(dir_path, 'db', f'{self.username}.db3')
                    self.database = ClientStorage(db_name_path)  # инициализируем db
        self.database_load()
        self.start_threads()
        return

    def load_keys(self):
        """Метод загрузки ключей из файла, если же файла нет, то генерирует новую пару."""
        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_file = os.path.join(dir_path, f'{self.username}.key')
        if not os.path.exists(key_file):
            self.keys = RSA.generate(2048, os.urandom)
            with open(key_file, 'wb') as key:
                key.write(self.keys.export_key())
        else:
            with open(key_file, 'rb') as key:
                self.keys = RSA.import_key(key.read())
        LOGGER.debug("Ключи загружены")
        return

    def transport_shutdown(self):
        """Метод остановки клиента"""
        self.running = False
        try:
            send_message(self.transport, self.create_exit_message())
        except OSError:
            pass
        LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, destination, message):
        """Метод отправки сообщения клиенту (на сервер, не р2р)"""
        message_dict = {
            DESTINATION: destination,
            SENDER: self.username,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username,
                MESSAGE_TEXT: message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        # Необходимо дождаться освобождения сокета для отправки сообщения
        # with self.sock_lock:
        send_message(self.transport, message_dict)
        LOGGER.info(f'Отправлено сообщение для пользователя {destination}')
        return

    def process_ans(self, message):
        """Метод обработчик входящих сообщений с сервера"""
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return RESPONSE_200
                # return
            elif message[RESPONSE] == 204:
                return RESPONSE_204
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_request()
                self.message_205.emit()
            else:
                raise ServerError('Ошибка связи с сервером')
            #     return
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION \
                in message and MESSAGE_TEXT in message[USER] and message[DESTINATION] == self.username:
            LOGGER.info(f'Сообщение из чята от {message[SENDER]}: {message[USER][MESSAGE_TEXT]}')
            self.new_message.emit(message[SENDER])
            with self.database_lock:
                try:
                    self.database.write_log(message[SENDER], 'me', message[USER][MESSAGE_TEXT])
                except:
                    LOGGER.error('Ошибка взаимодействия с базой данных')
                else:
                    LOGGER.debug('Сообщение получено')
                return
        else:
            return f'400 : {message[ERROR]}'
        raise ReqFieldMissingError(RESPONSE)

    def client_receiving(self):
        """Метод принимающий сообщения от сервера, работает в отдельном потоке"""
        LOGGER.debug('Запуск потока получения')
        LOGGER.info('Режим работы - прием сообщений')

        while self.running:
            time.sleep(1)
            with self.sock_lock:
                # Отдыхаем чуть-чуть и снова пробуем захватить сокет.
                # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
                try:
                    self.transport.settimeout(1)
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

    def get_clients(self, lock=False):
        """Метод запроса списка активных пользователей"""
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        request = self.create_presence(self.username)
        request[ACTION] = GETCLIENTS
        if lock:
            self.sock_lock.acquire()
        # with self.sock_lock:
        LOGGER.debug(f'отправка сообщения на сервер {request}')
        send_message(self.transport, request)
        ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 201:
            LOGGER.debug(f'getclients Получен ответ  - список пользователей сервера {ans[LIST]}')
            self.remote_users = [x for x in ans[LIST] if x != str(self.username)]
            LOGGER.debug('Получен список активных пользователей с сервера.')
        if lock:
            self.sock_lock.release()
        return

    def contacts_list_request(self, lock=False):
        """Метод запроса списка контактов"""
        self.database.contacts_clear()
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.username}')
        req = {
            ACTION: GETCONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        if lock:
            self.sock_lock.acquire()
        send_message(self.transport, req)
        ans = get_message(self.transport)
        #     LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST]:
                self.database.add_contact(contact)
        LOGGER.debug('Получен список контактов с сервера.')
        if lock:
            self.sock_lock.release()
        return

    def add_contact(self, contact):
        """Метод добавления пользователя в контакт лист"""
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with self.sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
            if RESPONSE in ans and ans[RESPONSE] == 200:
                pass
            else:
                raise ServerError('Ошибка создания контакта')
            # print('Удачное создание контакта.')
        return

    def remove_contact(self, contact):
        """Метод удаления пользователя из контакт-листа"""
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with self.sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
            if RESPONSE in ans and ans[RESPONSE] == 200:
                pass
            else:
                raise ServerError('Ошибка удаления клиента')
            # print('Удачное удаление контакта.')
        return

    @func_log
    def create_exit_message(self):
        """Метод формирующий сообщение о выходе ля отправки на сервер"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }

    def user_list_update(self, lock=False):
        """Метод получения активных пользователей с сервера"""
        # Загружаем список активных пользователей
        try:
            self.get_clients(lock)  # сообщаем что не нужно еще раз блокировать сокет
        except ServerError:
            LOGGER.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(self.remote_users)

    def database_load(self):
        """
        Метод стартовой загрузки клиентской базы данных.
        Загружает активыных пользователй и список контактов текущего пользователя с сервера
        """
        self.user_list_update(True)
        # Загружаем список контактов
        try:
            # with self.sock_lock:
            self.contacts_list_request(True)
        except ServerError:
            LOGGER.error('Ошибка запроса списка контактов.')
        else:
            return

    def get_start_params(self):
        """Метод получения стартовых параметров из командной строки"""
        LOGGER.debug("Попытка получить параметры запуска клиента")
        parser = create_arg_parser(DEFAULT_PORT, DEFAULT_IP_ADDRESS)
        namespace = parser.parse_args(sys.argv[1:])

        self.server_address = namespace.a
        self.server_port = namespace.p
        self.username = namespace.n
        self.password = namespace.w

        client_mode = namespace.m
        LOGGER.debug(f'Адрес и порт сервера {self.server_address}:{self.server_port}')

    def get_connect(self):
        """Метод сосздающий сокет подключения к серверу"""
        connected = False
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
        except ServerError as error:
            LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        except ReqFieldMissingError as missing_error:
            LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)
        else:
            connected = True
            LOGGER.debug('Установлено подключение к серверу')

        if connected:  # начинаем аутентификацию
            pass_hash = self.password.encode('utf-8')

    def start_threads(self):
        """Метод запускающий потоки получения и основного окна программы"""
        LOGGER.debug('Запуск потока получения')
        receive_thread = threading.Thread(target=self.client_receiving, daemon=True)
        receive_thread.start()
        main_window = ClientMainWindow(self.database, self)
        main_window.make_connection(self)
        main_window.setWindowTitle(f'Чат Программа alpha release - {self.username}')
        self.client_app.exec_()
        # Раз графическая оболочка закрылась, закрываем транспорт
        self.transport_shutdown()
        receive_thread.join()
        LOGGER.debug('Потоки запущены')
        return


def main():
    client = ClientTransport()
    client.gui_hello()


if __name__ == '__main__':
    main()
