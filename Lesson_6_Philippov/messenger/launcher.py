from subprocess import Popen, CREATE_NEW_CONSOLE


process = []
def run_msg(args):
    dont_stop = True
    while dont_stop:
        user_answer = input('Для запуска нажмие r, для остановки х: ')
        if user_answer == 'r':
            for item in args:
                # print(item)
                process.append(Popen('python3 client.py', creationflags=CREATE_NEW_CONSOLE))
                print(f'запускаем {item[1]}')
                # for line in process[0].stdout:
                #     result = chardet.detect(line)
                #     line = line.decode(result['encoding']).encode('utf-8')
                #     print(line.decode('utf-8'))
        elif user_answer == 'x':
            while process:
                target = process.pop()
                print(f' вышибаем {target}')
                target.kill()
            dont_stop = False





ARGS =(['python3','server.py'],['python3','client.py'])
run_msg(ARGS)