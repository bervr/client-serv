import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt


logger = logging.getLogger('client')


class DelContactDialog(QDialog):
    """Диалог выбора контакта для удаления"""
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(800, 300)
        self.setWindowTitle('Выберите контакт для удаления:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для удаления:', self)
        self.selector_label.setFixedSize(600, 30)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(600, 30)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(630, 30)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(630, 60)
        self.btn_cancel.clicked.connect(self.close)

        # заполнитель контактов для удаления
        self.selector.addItems(sorted(self.database.get_user_contacts()))


if __name__ == '__main__':
    # from client_database import ClientStorage
    # db = ClientStorage('user.db3')
    app = QApplication([])
    window = DelContactDialog(None)
    # window = DelContactDialog(db)
    window.show()
    app.exec_()
