import logging
import os
import select
import socket
import sys
import subprocess
from metaclasses import ServerVerifier
from descriptors import IsPortValid
import threading
from database import ServerStorage
import chardet
import configparser
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow

from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, MESSAGE_TEXT, \
    MESSAGE, SENDER, DESTINATION, RESPONSE_200, RESPONSE_400, EXIT, GETCLIENTS, \
    LIST, RESPONSE_CLIENTS, RESPONSE, GETCONTACTS, RESPONSE_202, ADD_CONTACT, REMOVE_CONTACT
from common.utils import get_message, send_message, create_arg_parser

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

    # Функция обновляющая список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        # new_connection = True
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающая окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
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

    # Запускаем GUI

    server_app.exec_()


class MsgServer(threading.Thread, metaclass=ServerVerifier):
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
            # если клиента нет в списке подключеных, то добавляем
            try:  #
                if message[USER][ACCOUNT_NAME] not in self.names.keys():
                    self.names[str(message[USER][ACCOUNT_NAME])] = client
                    # print(f'Подключен клиент {message[USER][ACCOUNT_NAME]}')
                    client_ip, client_port = client.getpeername()
                    self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                    send_message(client, RESPONSE_200)
                    with conflag_lock:
                        new_connection = True
                else:
                    response = RESPONSE_400 #todo добавить отключение неактивных reverse_ping
                    response[ERROR] = 'Имя пользователя уже занято'
                    send_message(client, response)
                    self.clients.remove(client)
                    client.close()
                return
            except Exception as err:
                print(1, err)

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
        if message[DESTINATION] in self.names.keys() and self.names[message[DESTINATION]] in to_send_data_list:
            # print(self.names[message[DESTINATION]])
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')

        # elif message[DESTINATION] == 'ALL':
        #     LOGGER.debug(f'Отправляем  сообщение {message} всем клиентам')
        #     for one_client in to_send_data_list:
        #         try:
        #             send_message(one_client, message)
        #             LOGGER.debug(f'Отправлено сообщение {message} клиенту {one_client}')
        #         except:
        #             LOGGER.info(f'{one_client.getpeername()} отключился от сервера')
        #             self.clients.remove(one_client)

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in to_send_data_list:
            raise ConnectionError
        else:

            LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')
            LOGGER.debug(
                f'на сервере остались {self.names.keys()} ')

    def run(self):
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


if __name__ == '__main__':
    main()
