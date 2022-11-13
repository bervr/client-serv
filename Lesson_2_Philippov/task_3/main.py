"""
3. Задание на закрепление знаний по модулю yaml.
 Написать скрипт, автоматизирующий сохранение данных
 в файле YAML-формата.
Для этого:

Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим в кодировке
ASCII(например, €);

Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла с помощью
параметра default_flow_style, а также установить возможность работы
с юникодом: allow_unicode = True;

Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""
import yaml


test_dict ={
    'catalog': [
        'audi',
        'volvo',
        'lada'
    ],
    'quantity': 11,
    'prices': {
        'audi': '12000€',
        'volvo': '150000₤',
        'lada': '650000₽'
    }
}
with open('data_write.yaml', 'w') as file:
    yaml.dump(test_dict, file, allow_unicode=True, default_flow_style=False)

with open('data_write.yaml', 'r') as file:
    readed = yaml.load(file, Loader=yaml.FullLoader)

print(readed == test_dict)
