import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt

logger = logging.getLogger('client')


class AddContactDialog(QDialog):
    """Диалог выбора контакта для добавления"""

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

    def possible_contacts_update(self):
        """Заполняет список возможных контактов разницей между всеми пользователями и множеством
        всех контактов и контактов клиента
        """
        self.selector.clear()
        contacts_list = set(self.database.get_user_contacts())
        users_list = set(self.database.get_users())
        # Удалим сами себя из списка пользователей, чтобы нельзя было добавить самого себя
        # Добавляем список возможных контактов
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        """Обновлялка возможных контактов. Обновляет таблицу известных пользователей,
        затем содержимое предполагаемых контактов
        """
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()
