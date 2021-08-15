import platform
from subprocess import Popen
if platform.system() == 'Windows':
    from subprocess import CREATE_NEW_CONSOLE
    enterpriter = 'python'
else:
    enterpriter = 'python3'
# print(platform.system())
process = []

def run_one(that: str):
    print(that)
    if platform.system() == 'Windows':
        process.append(Popen(that, creationflags=CREATE_NEW_CONSOLE))
    else:
        process.append(Popen(that, shell=True))


while True:
    user_answer = input("Запустить сервер(s)\nЗапустить 10 клиентов (c)\nЗакрыть все (x)\nВыйти(q): ")
    if user_answer == 'q':
        break
    elif user_answer == 's':
        run_one(f'{enterpriter} server.py')

    elif user_answer == 'c':
        for _ in range(7):
            run_one(f'{enterpriter} client.py')
        for _ in range(3):
            run_one(f'{enterpriter} client.py -m send')

    elif user_answer == 'x':
        for p in process:
            p.kill()
        process.clear()
