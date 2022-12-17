class IsPortValid:
    """Класс-дескриптор, проверяющий, что заданный порт является целым положительным числом"""
    def __get__(self, instance, owner):
        return instance.__dict__[self.my_attr]

    def __set__(self, instance, value):
        try:
            new_value = int(value)
        except ValueError:
            raise ValueError("Порт должен быть числом")
        else:
            if new_value != value:
                # raise ValueError("Порт должен быть ЦЕЛЫМ числом")
                print(f"Вы задали порт:{value}. Порт должен быть ЦЕЛЫМ числом. Будет установлен порт по умолчанию: 7777")
                new_value = 7777
            if value < 0:
                # raise ValueError("Порт не может быть отрицательным")
                print(f"Вы задали порт:{value}. Порт не может быть отрицательным. Будет установлен порт по умолчанию: "
                      f"7777")
                new_value = 7777

            instance.__dict__[self.my_attr] = new_value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr


class Wr:
    port = IsPortValid()

    def __init__(self, port):
        self.port = port

    def __str__(self):
        return f'new port is {self.port}'


if __name__ == '__main__':
    w = Wr(999)
    print(w)




