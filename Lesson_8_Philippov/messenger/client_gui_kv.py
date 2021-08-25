from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from client import MsgClient
import logs.conf.client_log_config
import logging



LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class FirstScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.client_name = ''


    def do_login(self):
        self.client_name = MsgClient.add_client_name(self, self.login.text)
        # MsgClient.client_name = MsgClient.add_client_name(self, self.login.text)
        # print(self.client_name)
        self.get_start_params()
        # self.manager.current = 'second'
        self.hello_user()

    def hello_user(self,**kwargs):
        super().__init__(**kwargs)
        # user_name = self.client_name
        # return self.hello_user()
        print(self.client_name, 'hello user')
        self.get_start_params()
        self.manager.current = 'second'


    def get_start_params(self):
        LOGGER.debug("Попытка получить параметры запуска клиента")
        self.server_address = self.server.text
        self.server_port = self.port.text

        LOGGER.debug(f'Адрес и порт сервера {self.server_address}:{self.server_port}')





class SecondScreen(FirstScreen):

    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.your_name.text = f"[color=000000]Вы видны всем под именем: {self.client_name}[/color]"
        # print(MsgClient().client_name)
        # self.contacts.add_widget(Button(text='all', on_press=self.select_user))
        self.clients = [123, 456, 789, 987, 654, 321, 505]
        for i in self.clients:
            self.contacts.add_widget(
                Button(text=f'{i}', on_press=self.select_user)
            )


    def previous_button(self):
        self.manager.current='first'

    def select_user(self,instance):
        # self.manager.current = 'third'
        print(instance.text)
        print(self.client_name)




class ClientApp(App):
    def build(self):
        #Добавляю красивый переход FadeTransition
        sm=ScreenManager(transition=FadeTransition())#Создаю менеджер экранов sm
        #обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        #в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        sm.add_widget(FirstScreen(name='first'))
        sm.add_widget(SecondScreen(name='second'))
        # sm.add_widget(ThirdScreen(name='third'))
        return sm

if __name__=="__main__":
    ClientApp().run()