import logging
import os
import select
import socket
import sys
import subprocess
import hmac
import binascii
import threading
import chardet
import configparser

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from .server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
dir_path = os.path.dirname(os.path.realpath(__file__))
import_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.append(import_path)
from common.metaclasses import ServerVerifier
from common.descriptors import IsPortValid
from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, MESSAGE_TEXT, \
    MESSAGE, SENDER, DESTINATION, RESPONSE_200, RESPONSE_400, EXIT, GETCLIENTS, \
    LIST, RESPONSE_CLIENTS, RESPONSE, GETCONTACTS, RESPONSE_202, ADD_CONTACT, REMOVE_CONTACT, PUBLIC_KEY_REQUEST, DATA, \
    RESPONSE_511, PUBLIC_KEY, RESPONSE_205
from common.utils import get_message, send_message, create_arg_parser
from .add_user import RegisterUser
from .remove_user import DelUserDialog
from .database import ServerStorage

LOGGER = logging.getLogger('server')  # забрали логгер из конфига

# Флаг, что был подключён новый пользователь, нужен чтобы не мучить DB
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


def arg_parser(default_port, default_address):
    LOGGER.info('Разбираем параметры для запуска сервера')
    parser = create_arg_parser(default_port, default_address)
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


def console(server):  # консольный вариант сервера
    help = 'help - справка\nexit - выход\ngetall - список всех пользователей\nconnected - подключенные сейчас\nlog - ' \
           'история сообщений '
    while True:  # поток взаимодействия с оператором сервера
        command = input("help - список всех команд. Введите команду: ")
        if command == 'exit':
            break
        elif command == 'help':
            print(help)
        elif command == 'connected':
            print('Будет реализовано в следующей версии программы')
            pass
        elif command == 'getall':
            for item in server.database.getall():
                print(item)
        elif command == 'log':
            name = input('Введите имя пользователя или нажмите enter если хотите вывести историю всех пользователей: ')
            history_log = server.database.history_log(name)
            for item in history_log:
                print(item)


def main():
    """
    Функция оркестратор запуска сервера. Получает параметры запуска из файла конфигаи
    стратует потоки обработки сообщений и графики
    """
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # listen_address, listen_port = arg_parser() # распарсили аргументы запуска
    # database = ServerStorage() # создали объект подключения к DB
    server = MsgServer(listen_address, listen_port, database)  # объект сервера Worker-a
    server.daemon = True
    server.start()  # запустили поток воркера
    # console(server)

    # Создаём графическое окружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        """
        Метод обновляющий список подключённых, проверяет флаг подключения, и
        если надо обновляет список
        """
        global new_connection
        # new_connection = True
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        """Метод создающий окно со статистикой клиентов"""
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()


    def server_config():
        """Метод создающий окно с настройками сервера"""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        """Метод сохранения настроек"""
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')


    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
    main_window.register_btn.triggered.connect(server.reg_user)
    main_window.remove_btn.triggered.connect(server.rem_user)

    # Запускаем GUI

    server_app.exec_()


class MsgServer(threading.Thread, metaclass=ServerVerifier):
    """main server messaging class"""
    # дескриптор порта
    listen_port = IsPortValid()

    def __init__(self, listen_address, listen_port, database):
        self.clients = []
        self.messages = []
        self.names = dict()
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.database = database
        if not 1023 < self.listen_port < 65535:
            LOGGER.critical(f'Невозможно запустить сервер на порту {self.listen_port}, порт занят или недопустим')
            sys.exit(1)
        super(MsgServer, self).__init__()

    def kill_server(self):  # todo вышибать  процесс сервера при занятии порта по эксепшену
        """Метод выключения сервера. Фильтрует процессы по порту и убивает"""
        # new_ping = subprocess.Popen(item, stdout=subprocess.PIPE)
        # for line in new_ping.stdout:
        #     result = chardet.detect(line)
        #     line = line.decode(result['encoding']).encode('utf-8')
        #     print(line.decode('utf-8'))

        that = ["netstat", "-aon", "|", "findstr", self.listen_port]
        # if platform.system() == 'Windows':
        str = subprocess.Popen(that, stdout=subprocess.PIPE)
        # else:
        #    str =  subprocess.Popen(that, stdout=subprocess.PIPE)
        result = chardet.detect(str)
        for line in str.stdout:
            print(line)
            line = line.decode(result['encoding']).encode('utf-8')
            print(line)

    def process_client_message(self, message, client):
        """ метод разбирающий клиентские сообщения. Принимает на вход словарь сообщения, проверяет их корректность,
         ничего не возвращает, отравляет ответ клиенту в виде словаря
        """
        global new_connection
        LOGGER.debug(f'Попытка разобрать клиентское сообщение: {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            self.autorize_user(message, client)
            return

        # Если это запрос активных клиентов
        if ACTION in message and message[ACTION] == GETCLIENTS and TIME in message and USER in message:
            # запрашиваем список подключеных клиентов
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
                LOGGER.debug(f'Отправка списка клиентов подключеных к серверу {RESPONSE_CLIENTS}')
                return
            except Exception as err:
                print(1, err)

        # если пришел EXIT:
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            with conflag_lock:
                self.database.user_logout(message[ACCOUNT_NAME])
                print(f'Отключен клиент {message[SENDER]}')
                this_one = self.names[message[ACCOUNT_NAME]]
                self.clients.remove(this_one)
                this_one.close()
                del this_one
                # with conflag_lock:
                new_connection = True
                LOGGER.info(f'Клиент {message[SENDER]} корректно отключен от сервера')
            return

        # Если это запрос контакт-листа
        elif ACTION in message and message[ACTION] == GETCONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST] = self.database.get_user_contacts(message[USER])
            try:
                send_message(client, response)
                LOGGER.info(f'Клиенту {message[SENDER]} отправлен словарь контактов {response[LIST]}')
                return
            except Exception as err:
                print(1, err)

            # Если это добавление контакта

        # Если это добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
             and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.del_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # если пришло сообщение добавляем его в очередь
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message[USER] \
                and DESTINATION in message and SENDER in message:
            # print(message)
            LOGGER.debug(f"От клиета {message[SENDER]} получено сообщение {message[USER][MESSAGE_TEXT]}")
            self.messages.append(message)
            self.database.process_message(
                message[SENDER], message[DESTINATION])
            # send_message(client, RESPONSE_200)
            return

        # Если это запрос публичного ключа пользователя
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message[USER]:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[USER][ACCOUNT_NAME])
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # если ничего не подошло:
        else:
            LOGGER.debug(f"{message} Некорректный запрос, вернуть 400")
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
        if message[DESTINATION] in self.names.keys() and self.names[message[DESTINATION]] in to_send_data_list:
            # print(self.names[message[DESTINATION]])
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in to_send_data_list:
            raise ConnectionError
        else:

            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')
            LOGGER.debug(
                f'на сервере остались {self.names.keys()} ')

    def autorize_user(self, message, client):
        """Метод реализующий авторизцию пользователей."""
        # Если имя пользователя уже занято-то возвращаем 400
        LOGGER.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400  # todo добавить отключение неактивных reverse_ping
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                LOGGER.debug(f'Имя пользователя уже занято {response}')
                send_message(client, response)
            except OSError:
                LOGGER.debug('OS Error')
                pass
            self.clients.remove(client)
            client.close()
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                LOGGER.debug(f'Unknown username, sending {response}')
                send_message(client, response)
            except OSError:
                pass
            self.clients.remove(client)
            client.close()
        else:
            LOGGER.debug('Пользователь получен, начинаем аутентификацию.')
            # если все ок - отвечаем 511 и запускаем аутентицикацию
            auth_message = RESPONSE_511
            # рандомная строка в hex представлении соль для проверки ключа
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            auth_message[DATA] = random_str.decode('ascii')
            # взяли хеш пароля из базы и хешируем с ранее полученой рандомной строкой, сохраняем серверную версию ключа
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            # для красоты и удобства получаем дайджест
            digest = hash.digest()
            LOGGER.debug(f'соль для клиента = {auth_message}')
            try:
                # отсылаем клиенту соль
                send_message(client, auth_message)
                ans = get_message(client)
            except OSError as err:
                LOGGER.debug('Ошибка проверки подлинности, data:', exc_info=err)
                client.close()
                return
            # полученый ответ клиента преобразуем из ascii  в дайджест
            client_digest = binascii.a2b_base64(ans[DATA])
            # Сверяем то что прислал клиент с тем что вычислил сервер.
            # compare_digest используем чтобы предотвратить атаку по веремени
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(
                    digest, client_digest):
                LOGGER.debug(f"От клиента пришло  {ans}")
                # если все в порядке до добавляем клиента в список активных
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                # и шлем ему 200-OK
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    # если не получилось отправить 200, то удаляем, значит не судьба
                    self.remove_client(message[USER][ACCOUNT_NAME])
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                # сохраняем новый
                new_pub_key = self.database.get_pubkey(message[USER][ACCOUNT_NAME])
                if message[USER][PUBLIC_KEY] != new_pub_key:
                    self.database.user_login(
                        message[USER][ACCOUNT_NAME],
                        client_ip,
                        client_port,
                        message[USER][PUBLIC_KEY])
                message = {}
                return
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
                self.clients.remove(client)
                client.close()

    def service_update_lists(self):
        """ Метод реализующий отправки сервисного сообщения 205 клиентам. """
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])

    def run(self):
        """Метод запуска поотка обработки сообщения"""
        global new_connection
        LOGGER.info('Попытка запуска сервера')
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # проверка метакласса
            transport.bind((self.listen_address, self.listen_port))
            transport.listen(MAX_CONNECTIONS)
            transport.settimeout(0.1)
            # transport.connect('192.168.22.1', '80') # проверка метакласса

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
        # self.kill_server()

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
            except OSError:
                pass

            # парсим сообщения клиентов и если есть сообщения кладем их в словарь сообщений,
            # если ошибка - исключаем клиента
            if incoming_data_list:
                for sended_from_client in incoming_data_list:
                    # print(get_message(sended_from_client))
                    try:
                        self.process_client_message(get_message(sended_from_client), sended_from_client)
                    except Exception as err:
                        print(err)

                        LOGGER.info(f'{sended_from_client.getpeername()} отключился от сервера')
                        new_connection = True
                        self.clients.remove(sended_from_client)

            for one_message in self.messages:
                try:
                    LOGGER.debug(f'Обработка сообщения {one_message}')
                    self.process_message(one_message, to_send_data_list)
                except Exception:
                    LOGGER.info(f'Соединение с {one_message[DESTINATION]} разорвано')
                    try:
                        self.clients.remove(self.names[one_message[DESTINATION]])
                        del self.names[one_message[DESTINATION]]
                    except Exception:
                        pass  # todo добавить отбойник что сообщение не доставлено, или сохранение в очередь
            self.messages.clear()

    def remove_client(self, client):
        """Метод удаления клиента"""
        LOGGER.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()
        return

    def reg_user(self):
        """Метод создающий окно регистрации пользователя."""
        global reg_window
        reg_window = RegisterUser(self.database, self)
        reg_window.show()

    def rem_user(self):
        """Метод создающий окно удаления пользователя."""
        global rem_window
        rem_window = DelUserDialog(self.database, self)
        rem_window.show()


if __name__ == '__main__':
    main()
