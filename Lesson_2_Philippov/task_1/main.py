"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt,
info_3.txt и формирующий новый «отчетный» файл в формате CSV.

Для этого:

Создать функцию get_data(), в которой в цикле осуществляется перебор файлов
с данными, их открытие и считывание данных. В этой функции из считанных данных
необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения каждого параметра поместить в соответствующий список. Должно
получиться четыре списка — например, os_prod_list, os_name_list,
os_code_list, os_type_list. В этой же функции создать главный список
для хранения данных отчета — например, main_data — и поместить в него
названия столбцов отчета в виде списка: «Изготовитель системы»,
«Название ОС», «Код продукта», «Тип системы». Значения для этих
столбцов также оформить в виде списка и поместить в файл main_data
(также для каждого файла);

Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(),
а также сохранение подготовленных данных в соответствующий CSV-файл;

Пример того, что должно получиться:

Изготовитель системы,Название ОС,Код продукта,Тип системы

1,LENOVO,Windows 7,00971-OEM-1982661-00231,x64-based

2,ACER,Windows 10,00971-OEM-1982661-00231,x64-based

3,DELL,Windows 8.1,00971-OEM-1982661-00231,x86-based

Обязательно проверьте, что у вас получается примерно то же самое.

ПРОШУ ВАС НЕ УДАЛЯТЬ СЛУЖЕБНЫЕ ФАЙЛЫ TXT И ИТОГОВЫЙ ФАЙЛ CSV!!!
"""
import csv, chardet, re

start_list = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']

def get_data():
    for i in range(1, 4):
        with open (f'info_{i}.txt', 'rb') as file:
            try_encode = file.read()
            result = chardet.detect(try_encode)
        with open (f'info_{i}.txt', encoding=result['encoding']) as file:
            test_list = start_list.copy()
            readed = file.readlines()
            for line in readed:
                for item in test_list:
                    if item in line:
                        # my_catch = re.search(f"'{item}:\s\w*'", line)
                        my_res = re.split('\s{2,}', line.split(f"'{item}: '")[0], 2)[1]
                        # print(re.split(f"'{item}:\s*\B", line))
                        test_list.remove(item)
                        print(my_res)




def write_to_csv():
    pass


get_data()