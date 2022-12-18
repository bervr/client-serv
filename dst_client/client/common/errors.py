class NonDictInputError(Exception):
    """Исключение - аргумент функции не является словарем"""
    def __str__(self):
        return 'Аргумент функции должен быть словарем'


class IncorrectDataReceivedError(Exception):
    """Исключение - некорректное сообщение"""
    def __str__(self):
        return 'Принято некорректное сообщение от удаленного компьютера'


class ReqFieldMissingError(Exception):
    """Исключение - в запросе отсутствует обязательное поле"""
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
