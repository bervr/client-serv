class NonDictInputError(Exception):
    def __str__(self):
        return 'Аргумент функции должен быть словарем'


class IncorrectDataReceivedError(Exception):
    def __str__(self):
        return 'Принято некорректное сообщение от удаленного компьютера'


class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}'

class ServerError(Exception):
    """Исключение - ошибка сервера"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
