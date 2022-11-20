# На стороне сервера БД содержит следующие таблицы:
# a) клиент:
# * логин;
# * информация.
# b) история клиента:
# * время входа;
# * ip-адрес.
# c) список контактов (составляется на основании выборки всех записей с id_владельца):
# * id_владельца;
# * id_клиента.
from time import strftime

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from common.variables import SERVER_DATABASE

Base = declarative_base()


class ServerStorage:
    class Users(Base):
        __tablename__ = 'Users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        info = Column(String)

        def __init__(self, login, info=''):
            self.login = login
            self.info = info

        def __repl__(self):
            return f'User{self.id}({self.login})'

    class UserLoginHistory(Base):
        __tablename__ = 'user_login_history'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'))
        ipaddress = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ipaddress, port, login_time):
            self.user_id = user_id
            self.ipaddress = ipaddress
            self.port = port
            self.login_time = login_time

        def __repl__(self):
            return f'User{self.user_id}-ip{self.ipaddress}:{self:port}-{self.login_time}'

    def __init__(self):
        self.engine = create_engine(SERVER_DATABASE,
                                    echo=False,
                                    connect_args={'check_same_thread': False}
                                    )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def user_login(self, username, ipaddress, port):
        find_login = self.session.query(self.Users).filter_by(login=username)
        # ищем пользователя с таким же логином
        if find_login.count():  # если есть то берем его логин и записываем в историю входа
            user = find_login.first()
            new_log_record = self.UserLoginHistory(user.id, ipaddress, port, datetime.datetime.now())
        else: # если нет то создаем нового
            new_user = self.Users(username)
            self.session.add(new_user)
            self.session.commit()  # коммитим чтобы был объект на который сошлется foreignkey
            # и записываем в историю входа
            new_log_record = self.UserLoginHistory(new_user.id, ipaddress, port, datetime.datetime.now())
        self.session.add(new_log_record)
        self.session.commit()

    def getall(self):
        all_users = self.session.query(self.Users.id, self.Users.login).all()
        return all_users

    def history_log(self, name=''):
        logs = self.session.query(self.Users.login, self.UserLoginHistory.ipaddress, self.UserLoginHistory.port,
                                  self.UserLoginHistory.login_time).join(self.Users)

        return logs.all() if name == '' else logs.filter_by(login=name).all()


if __name__ == '__main__':
    client = ServerStorage()

    # client.user_login('ivanov', '127.0.0.1', 55)
    # print(client.getall())
    # print(client.history_log())
    # print(client.history_log('ivanov'))

