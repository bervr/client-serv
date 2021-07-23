"""
Задание 4.

Преобразовать слова «разработка», «администрирование», «protocol»,
«standard» из строкового представления в байтовое и выполнить
обратное преобразование (используя методы encode и decode).

Подсказки:
--- используйте списки и циклы, не дублируйте функции
"""


def en_de_code(items, direction):
    result = []
    for item in items:
        if direction == 'encode':
            result.append(item.encode('utf-8'))
        elif direction == 'decode':
            result.append(item.decode('utf-8'))
    print(result)
    return result


if __name__ == "__main__":
    my_list = ['разработка', 'администрирование', 'protocol', 'standard']

    my_list = en_de_code(my_list, 'encode')
    my_list = en_de_code(my_list, 'decode')
