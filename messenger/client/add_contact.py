import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('client')


# Диалог выбора контакта для добавления
class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(800, 300)
        self.setWindowTitle('Выберите контакт для добавления:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(500, 30)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(500, 30)
        self.selector.move(10, 50)

        self.btn_refresh = QPushButton('Обновить список', self)
        self.btn_refresh.setFixedSize(200, 40)
        self.btn_refresh.move(60, 100)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(100, 40)
        self.btn_ok.move(530, 50)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 40)
        self.btn_cancel.move(530, 90)
        self.btn_cancel.clicked.connect(self.close)

        # Заполняем список возможных контактов
        self.possible_contacts_update()
        # Назначаем действие на кнопку обновить
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    # Заполняем список возможных контактов разницей между всеми пользователями и
    def possible_contacts_update(self):
        self.selector.clear()
        # множества всех контактов и контактов клиента
        contacts_list = set(self.database.get_user_contacts())
        users_list = set(self.database.get_users())
        print(users_list)
        # Удалим сами себя из списка пользователей, чтобы нельзя было добавить самого себя
        # users_list.remove(self.transport.username)

        # Добавляем список возможных контактов
        self.selector.addItems(users_list - contacts_list)

    # Обновлялка возможных контактов. Обновляет таблицу известных пользователей,
    # затем содержимое предполагаемых контактов
    def update_possible_contacts(self):
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()

# if __name__ == '__main__':
#     from client_database import ClientStorage
#     import transport
#     tr = transport.ClientTransport()
#     db = ClientStorage('user.db3')
#     app = QApplication([])
#     window = AddContactDialog(tr, db)
#     # window = DelContactDialog(None)
#     window.show()
#     app.exec_()
