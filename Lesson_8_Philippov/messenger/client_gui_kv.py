import datetime
import sys
import time
from threading import Thread

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from client import MsgClient
import logs.conf.client_log_config
import json
import logging
from common.utils import get_message, send_message
from common.variables import RESPONSE_200, RESPONSE, SENDER, USER, MESSAGE_TEXT, ACCOUNT_NAME, TIME, ACTION, \
    DESTINATION, MESSAGE, MYCOLOR, NOTMYCOLOR

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class FirstScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.obj = new_msg

    def get_params(self):
        self.obj.client_name = self.login.text
        self.obj.server_port = self.port.text
        self.obj.server_address = self.server.text
        # print(self.obj.client_name, self.obj.server_address, self.obj.server_port)
        return self.obj


class SecondScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.msg_obj = new_msg
        # self.clients = [123, 456, 789, 987, 654, 321, 505, 18, 14, 45]
        # # self.clients = []

    def check_name(self):
        """проверяем что это имя не занято"""
        print(self.msg_obj.client_name)
        answer = self.msg_obj.hello(self.msg_obj.client_name)
        if answer != RESPONSE_200:
            self.revert()
        else:
            self.msg_obj.start_threads()
            return

    def revert(self):
        """ возвращает на экран логина"""
        print('имя уже занято')  # todo  починить надпись о том что имя уже занято
        # self.parent.screens[0].login.text = ''
        # self.parent.screens[0].login.hint_text = f"[color=363636]Нельзя зарегистрироваться под именем  " \
        #                       f"{self.msg_obj.client_name} это имя уже занято[/color]"
        self.manager.current = 'first'

    def render_contacts(self):
        """ загружаем с сервера и перерисовываем контакты"""
        # self.update_userlist()
        self.msg_obj.get_clients()
        # print(self.msg_obj.remote_users)
        for i in range(len(self.ids.contacts.children)):
            self.ids.contacts.remove_widget(self.ids.contacts.children[-1])

        self.your_name.text = f"[color=000000]Вы видны всем под именем: " \
                              f"{self.msg_obj.client_name if self.msg_obj.client_name else 'Guest'}[/color]"
        print(self.msg_obj.history)

        if self.msg_obj.remote_users != []:
            for i in self.msg_obj.remote_users:
                self.contacts.add_widget(
                    Button(text=f'{i}', size_hint_y=None, height=40, on_press=self.select_user)
                )
                # todo scrollview

    def previous_button(self):
        self.manager.current = 'first'

    def select_user(self, instance):
        """ выбор контакта с которым бутем переписываться, подгрузка его истории"""
        self.msg_obj.destination = instance.text
        # print(instance.text)
        self.print_chat()
        # print(self.msg_obj.client_name)

    def send(self):
        self.msg_obj.message = self.send_text.text
        self.msg_obj.to_send = True
        self.msg_obj.save_to_history(self.msg_obj.destination)
        self.send_text.text = ''
        self.print_chat()

    def print_chat(self):
        self.chat.text = ''
        self.chat.text = self.msg_obj.parse_chat()



class MyMsg(MsgClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.destination = None
        self.message = ''
        self.to_send = False
        self.history = {}  # {contact:{1:[time, from, text],2:[time, from, text],..}}
        self.history = {'bervr': {0: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'bervr', 'привет'],
              1: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'bervr', 'как дела?'],
              2: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'me', 'привет'],
              3: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'me', 'норм, как сам?'],
              4: [datetime.datetime(2017, 4, 5, 10, 17, 8, 24239), 'bervr', 'дело есть...'],
              }}

    def save_to_history(self, another, who='me'):
        """ сохраняем историю чата, на вход принимает имя контакта, и имя отправителя"""
        if another not in self.history.keys():
            self.history[another] = {}
        chat = self.history.get(another)
        msg_count = len(chat.keys())
        chat[msg_count] = [datetime.datetime.today(), who, self.message]
        # print(chat)
        # print(self.history)


    def parse_chat(self):
        chat = self.history.get(self.destination)
        text = ''
        try:
            for key, value in chat.items():
                if value[1] =='me':
                    twit = f'[color={MYCOLOR}]{(value[0]).strftime("%Y-%m-%d %H:%M:%S")} from {value[1]}: {value[2]}[/color]\n'
                else:
                    twit = f'[color={NOTMYCOLOR}]{(value[0]).strftime("%Y-%m-%d %H:%M:%S")} from {value[1]}: {value[2]}[/color]\n'

                # print(twit)
                text += twit
        except Exception:
            pass
        return text


    def create_message(self):
        out = {
            DESTINATION: self.destination,
            SENDER: self.client_name,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name,
                MESSAGE_TEXT: self.message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {out}')
        return out

    def client_receiving(self):
        LOGGER.info('Режим работы - прием сообщений')
        while True:
            try:
                answer = get_message(self.transport)
                print(answer)
                if RESPONSE in answer:
                    self.process_ans(answer)
                    # print(self.remote_users)
                else:
                    if answer[SENDER] != self.client_name:
                        if answer[DESTINATION] == 'ALL':
                            self.save_to_history('ALL', answer[SENDER])
                        else:
                            self.save_to_history(answer[SENDER], answer[SENDER])
                    # print(f'\nUser {answer[SENDER]} sent: {answer[USER][MESSAGE_TEXT]}')
                    LOGGER.info(f'Сообщение из чята от {answer[SENDER]}: {answer[USER][MESSAGE_TEXT]}')
                    # print(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        while True:
            if self.to_send:
                try:
                    send_message(self.transport, self.create_message())
                    self.to_send = False
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                    sys.exit(1)

    def start_threads(self):
        """ переопределили родительский метод чтобы программа не блокировалась при запуске слушателей"""
        receive_thread = Thread(target=self.client_receiving, daemon=True)
        send_thread = Thread(target=self.client_sending, daemon=True)
        receive_thread.start()
        send_thread.start()
        # receive_thread.join()
        # send_thread.join()
        # return


class ClientApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build(self):
        """ выстраиваем интерфейс"""
        # Добавляю красивый переход FadeTransition
        sm = ScreenManager(transition=FadeTransition())  # Создаю менеджер экранов sm
        # обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        # в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        self.new_msg = MyMsg()
        # new_msg = MsgClient()

        first_screen = FirstScreen(self.new_msg, name='first')
        second_screen = SecondScreen(self.new_msg, name='second')
        sm.add_widget(first_screen)
        sm.add_widget(second_screen)
        self.title = 'MeowMessenger'
        # self.icon = 'myicon.png'
        return sm


if __name__ == "__main__":
    ClientApp().run()
    # ClientApp().run_threads()
