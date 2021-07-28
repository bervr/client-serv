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
import chardet
import csv
import re

# start_list = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
start_dict = {'sys_prod': 'Изготовитель системы', 'os_name': 'Название ОС', 'os_code': 'Код продукта',
              'os_type': 'Тип системы'}
# result = dict.fromkeys(start_dict, []) # <- ох и намучался я с этим списком...
result = {k: [] for k in start_dict}  # <- так создается по отдельному списку для каждого ключа


def get_data(result, start_dict):
    for i in range(1, 4):
        with open(f'info_{i}.txt', 'rb') as file:
            try_encode = file.read()
            codepage = chardet.detect(try_encode)
        with open(f'info_{i}.txt', encoding=codepage['encoding']) as file:
            test_dict = start_dict.copy()
            readed = file.readlines()
            for i in range(len(test_dict)):
                key, value = test_dict.popitem()
                for line in readed:
                    if value in line:
                        # my_res = re.split('\s{2,}', line.split(f"'{value}: '")[0], 2)[1]
                        my_res = re.split(':\s{2,}', line)[1].strip('\n')
                        result[key].append(my_res)
                        break
    with open('main_data', 'w', encoding='utf-8') as new_file:
        main_data = []
        main_data.append([','.join(start_dict.values())])
        for i in range(len(list(result.values())[0])):
            main_data.append([','.join({key: value[i] for key, value in result.items()}.values())])
        for item in main_data:
            new_file.writelines(f"{','.join(item)}\n")
        return main_data


def write_to_csv(to_write_filename, open_file='main_data'):
    # new_list = get_data(result, start_dict)
    get_data(result, start_dict)
    new_list = []
    with open(open_file, 'r', encoding='utf-8') as file:
        while True:
            line = file.readline()
            if not line:
                break
            print(line.strip().split(','))
            new_list.append(line.strip().split(','))
    # print(new_list)

    with open(to_write_filename, 'w') as file:
        file_to_write = csv.writer(file)
        for row in new_list:
            file_to_write.writerow(row)


write_to_csv('report.csv')
