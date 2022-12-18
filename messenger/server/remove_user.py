from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt


class DelUserDialog(QDialog):
    """
    Класс - диалог выбора контакта для удаления.
    """

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setFixedSize(640, 280)
        self.setWindowTitle('Удаление пользователя')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel(
            'Выберите пользователя для удаления:', self)
        self.selector_label.setFixedSize(400, 40)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(400, 40)
        self.selector.move(10, 50)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 40)
        self.btn_ok.move(430, 50)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 40)
        self.btn_cancel.move(430, 90)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):
        """Метод заполняющий список пользователей."""
        self.selector.addItems([item[0]
                                for item in self.database.users_list()])

    def remove_user(self):
        """Метод - обработчик удаления пользователя."""
        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)
        # Рассылаем клиентам сообщение о необходимости обновить справочники
        self.server.service_update_lists()
        self.close()
