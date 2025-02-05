import subprocess


def check_process():
    command = 'ps aux | grep "[p]ython3 main.py"'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout.strip()

    if output:
        print("Найденные процессы:")
        print(output)
        print(len(output))
        print(len(output.split("\n")))
        return True
    else:
        print("Процесс main.py не найден.")
        return False
