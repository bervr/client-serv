"""
2. Задание на закрепление знаний по модулю json. Есть файл orders
в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий
его заполнение данными.

Для этого:
Создать функцию write_order_to_json(), в которую передается
5 параметров — товар (item), количество (quantity), цена (price),
покупатель (buyer), дата (date). Функция должна предусматривать запись
данных в виде словаря в файл orders.json. При записи данных указать
величину отступа в 4 пробельных символа;
Проверить работу программы через вызов функции write_order_to_json()
с передачей в нее значений каждого параметра.

ПРОШУ ВАС НЕ УДАЛЯТЬ ИСХОДНЫЙ JSON-ФАЙЛ
ПРИМЕР ТОГО, ЧТО ДОЛЖНО ПОЛУЧИТЬСЯ

{
    "orders": [
        {
            "item": "printer",
            "quantity": "10",
            "price": "6700",
            "buyer": "Ivanov I.I.",
            "date": "24.09.2017"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        }
    ]
}

вам нужно подгрузить JSON-объект
и достучаться до списка, который и нужно пополнять
а потом сохранять все в файл
"""
import json
from datetime import datetime


def write_order_to_json(item, quantity, price, buyer, date):
    with open('orders.json') as file:
        json_obj = json.load(file)
        # print(json_obj['orders'])
        new_item = {
            'item': item,
            'quantity': quantity,
            'price': price,
            'buyer': buyer,
            'date': date
        }
    data = json_obj['orders'].append(new_item)
    print(json_obj)
    with open('orders.json', 'w', encoding='utf-8') as file:
        json.dump(json_obj, file, sort_keys=True, indent=4)




write_order_to_json(1,1,1,['Basiliev','Basil'], f'{datetime.now().date()}' )
