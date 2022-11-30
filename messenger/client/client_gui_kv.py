import datetime
import sys
import time
from threading import Thread

from kivy.app import App
from kivy.base import runTouchApp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image

from client_run import MsgClient
import logs.conf.client_log_config
import json
import logging
from common.utils import get_message, send_message
from common.variables import RESPONSE_200, RESPONSE, SENDER, USER, MESSAGE_TEXT, ACCOUNT_NAME, TIME, ACTION, \
    DESTINATION, MESSAGE, MYCOLOR, NOTMYCOLOR
from kivy.uix.button import Button
from kivy.properties import StringProperty

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class LetterButton(Button):
    pass
 #but if you want to set the image of the button remove the pass and uncomment the following:
    #image_path = StringProperty('')

    def __init__(self,image_path, **kwargs):
        super(LetterButton, self).__init__(**kwargs)
        self.image_path = image_path



class FirstScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.obj = new_msg

    def get_params(self):
        """ получаем параметры запуска - сервер, порт и логин"""
        self.obj.client_name = self.login.text
        self.obj.server_port = self.port.text
        self.obj.server_address = self.server.text
        return self.obj



class SecondScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.msg_obj = new_msg
        # self.clients = [123, 456, 789, 987, 654, 321, 505, 18, 14, 45]
        # тестовые контакты

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
        print('имя уже занято')
        self.manager.screens[0].login.text = ''
        self.manager.screens[0].login.hint_text = f"Нельзя зарегистрироваться под именем\n " \
                              f"{self.msg_obj.client_name} это имя уже занято"
        self.manager.current = 'first'

    def update(self):
        """загружаем с сервера контакты"""
        self.msg_obj.get_clients()
        self.render_contacts()

    def render_contacts(self):
        """ перерисовываем контакты"""
        not_viewed = self.msg_obj.find_new_messages()
        for i in range(len(self.ids.contacts.children)):
            self.ids.contacts.remove_widget(self.ids.contacts.children[-1])

        self.your_name.text = f"[color=000000]Вы видны всем под именем: " \
                              f"{self.msg_obj.client_name if self.msg_obj.client_name else 'Guest'}[/color]"

        if self.msg_obj.remote_users != []:
            for i in self.msg_obj.remote_users:
                if i in not_viewed:
                    self.contacts.add_widget( # todo иконка непрочитаных на кнопке
                        Button(text=f'{i}',
                               size_hint_y=None, height=40, on_press=self.select_user,
                    ))
                else:
                    self.contacts.add_widget(
                        Button(text=f'{i}', size_hint_y=None, height=40, on_press=self.select_user)
                    )

    def previous_button(self):
        self.manager.current = 'first'

    def select_user(self, instance):
        """ выбор контакта с которым бутем переписываться, показ его истории,
        покраска кнопки и вызов сброса покраски остальных кнопок, а также сброс конверта"""
        self.msg_obj.destination = instance.text
        instance.background_color = (.0, .88, .88, .85)
        self.clear_selection(instance)
        self.print_chat()
        self.chat_name.text = f"[color=000000]Чат с {instance.text}:[/color]"

    def clear_selection(self, instance):
        """ очистка раскраски  не выбраных в данный момент кнопок"""
        if instance != self.all_button:
            self.all_button.background_color = (.88, .88, .88, .85)
        for i in range(len(self.ids.contacts.children)):
            if instance != self.ids.contacts.children[i]:
                self.ids.contacts.children[i].background_color = (.88, .88, .88, .85)

    def send(self):
        """ отправка введенного сообщения и сохранение в историю"""
        self.msg_obj.message = self.send_text.text
        self.msg_obj.to_send = True
        self.msg_obj.save_to_history(self.msg_obj.message, True, self.msg_obj.destination)
        self.send_text.text = ''
        self.print_chat()

    def print_chat(self):
        """ вывод истории текста на экран"""
        self.chat.text = ''
        self.chat.text = self.msg_obj.parse_chat()


class MyMsg(MsgClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.destination = None
        self.message = ''
        self.incoming_message = ''
        self.to_send = False
        self.history = {}  # {contact:{1:[time, from, text],2:[time, from, text],..}}
        self.history = {'bervr': {'viewed': False, 'messages': {
            0: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'bervr', 'привет'],
            # 1: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'bervr', 'как дела?'],
            # 2: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'me', 'привет'],
            # 3: [datetime.datetime(2017, 4, 5, 0, 17, 8, 24239), 'me', 'норм, как сам?'],
            # 4: [datetime.datetime(2017, 4, 5, 10, 17, 8, 24239), 'bervr', 'дело есть...'],
        }}}

    def save_to_history(self, message, viewed, another, who='me'):
        """ сохраняем историю чата, на вход принимает имя контакта, и имя отправителя, статус прочитанности"""
        if another not in self.history.keys():
            self.history[another] = {}
            self.history.get(another)['messages'] = {}
        chat = self.history.get(another)
        chat['viewed'] = viewed
        add_msg = self.history.get(another).get('messages')
        msg_count = len(add_msg.keys()) + 1
        add_msg.update({msg_count: [datetime.datetime.today(), who, message]})
        # add_msg[msg_count] =
        # print(chat)
        # print(self.history)

    def find_new_messages(self):
        not_viewed = []
        for key, value in self.history.items():
            if not value['viewed']:
                not_viewed.append(key)
        return not_viewed

    def parse_chat(self):
        chat = self.history.get(self.destination)
        text = ''
        if chat:
            chat['viewed'] = True
            try:
                for key, value in chat['messages'].items():
                    if value[1] == 'me':
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
                        self.incoming_message = answer[USER][MESSAGE_TEXT]
                        print(self.incoming_message)
                        if answer[DESTINATION] == 'ALL':
                            self.save_to_history(self.incoming_message, False, 'ALL', answer[SENDER])
                        else:
                            self.save_to_history(self.incoming_message, False, answer[SENDER], answer[SENDER])
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
        """ переопределили родительский метод чтобы графика не блокировалась при запуске слушателей"""
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
        # добавляем красивый переход FadeTransition
        sm = ScreenManager(transition=FadeTransition())
        # создаем менеджер экранов sm
        # обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        # в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        self.new_msg = MyMsg()

        first_screen = FirstScreen(self.new_msg, name='first')
        second_screen = SecondScreen(self.new_msg, name='second')
        sm.add_widget(first_screen)
        sm.add_widget(second_screen)
        self.title = 'MeowMessenger'
        self.icon = 'letter.png'
        return sm


if __name__ == "__main__":
    runTouchApp(ClientApp().run())
