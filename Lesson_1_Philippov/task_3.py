"""
Задание 3.

Определить, какие из слов «attribute», «класс», «функция», «type»
невозможно записать в байтовом типе с помощью маркировки b'' (без encode decode).

Подсказки:
--- используйте списки и циклы, не дублируйте функции
--- обязательно!!! усложните задачу, "отловив" и обработав исключение,
придумайте как это сделать
"""
import chardet


def check_encode(items):
        for item in items:
            item_encoding = chardet.detect(item)
            print(item, item_encoding)
        # print(1)


my_list = ['attribute', 'класс', 'функция', 'type']
check_encode(my_list)
