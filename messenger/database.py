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

    class ActiveUsers(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'), unique=True)
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

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'))
        contact_id = Column(ForeignKey('Users.id'))

        def __init__(self, user_id, contact_id):
            self.user_id = user_id
            self.contact_id = contact_id

        def __repl__(self):
            return f'User{self.user_id}-contact{self.contact_id}'



    def __init__(self):
        self.engine = create_engine(SERVER_DATABASE,
                                    echo=False,
                                    connect_args={'check_same_thread': False}
                                    )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete() # очищаем таблицу активных юзеров при старте
        self.session.commit()

    def user_login(self, username, ipaddress, port):
        find_login = self.session.query(self.Users).filter_by(login=username)
        # ищем пользователя с таким же логином
        if find_login.count():  # если есть то берем его логин и записываем в историю входа и в активные
            user = find_login.first()
            new_log_record = self.UserLoginHistory(user.id, ipaddress, port, datetime.datetime.now())
            new_active = self.ActiveUsers(user.id, ipaddress, port, datetime.datetime.now())
        else: # если нет то создаем нового
            new_user = self.Users(username)
            self.session.add(new_user)
            self.session.commit()  # коммитим чтобы был объект на который сошлется foreignkey
            # и записываем в историю входа
            new_log_record = self.UserLoginHistory(new_user.id, ipaddress, port, datetime.datetime.now())
            new_active = self.ActiveUsers(new_user.id, ipaddress, port, datetime.datetime.now())
        self.session.add(new_log_record)
        self.session.add(new_active)
        self.session.commit()

    def getactive(self):
        active_users = self.session.query(self.Users.login, self.ActiveUsers.ipaddress, self.ActiveUsers.port,
                                          self.ActiveUsers.login_time).join(self.Users).all()
        return active_users

    def getall(self):
        all_users = self.session.query(self.Users.id, self.Users.login).all()
        return all_users

    def history_log(self, name=''):
        logs = self.session.query(self.Users.login, self.UserLoginHistory.ipaddress, self.UserLoginHistory.port,
                                  self.UserLoginHistory.login_time).join(self.Users)

        return logs.all() if name == '' else logs.filter_by(login=name).all()

    def user_logout(self, user_id):
        try:
            get_login = self.session.query(self.ActiveUsers).filter_by(user_id=user_id).first()
        except:
            pass
        else:
            self.session.delete(get_login)
            self.session.commit()

    def add_contact(self, user_id, contact_id):

        find_contact = self.session.query(self.Contacts.user_id, self.Contacts.contact_id).filter_by(user_id=user_id)\
                .filter_by(contact_id=contact_id).all()
        if find_contact:
            print('Такой контакт уже есть')
        else:
            new_contact = self.Contacts(user_id, contact_id)
            self.session.add(new_contact)
            self.session.commit()

    def del_contact(self, user_id, contact_id):
        self.session.query(self.Contacts).filter_by(user_id=user_id).filter_by(contact_id=contact_id).delete()
        self.session.commit()

    def get_user_contacts(self, user_id):
        try:
            contacts = self.session.query(self.Contacts.user_id, self.Contacts.contact_id).filter_by(user_id=user_id).all()
        except:
            contacts = []
        return contacts


if __name__ == '__main__':
    client = ServerStorage()
    # print(client.getactive())
    client.user_login('ivanov', '127.0.0.1', 55)
    client.user_login('pppetrov', '127.0.0.1', 11)
    client.user_login('kuznetsov', '127.0.0.127', 99)
    client.user_login('pppetroff', '127.0.0.99', 22)
    # print(client.getall()))
    print(client.getactive())
    # client.user_logout(1)
    # print(client.getactive())
    # print(client.history_log())
    # print(client.history_log('ivanov'))
    print(client.get_user_contacts(1))
    client.add_contact(1, 2)
    client.add_contact(1, 3)
    client.add_contact(1, 4)
    print(client.get_user_contacts(1))
    client.del_contact(1, 2)
    client.del_contact(1, 4)
    client.add_contact(1, 3)
    client.del_contact(1, 4)
    print(client.get_user_contacts(1))



