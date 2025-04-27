from storage.storage_system import StorageSystem
def start():
    system = StorageSystem()
    while True:
        inp = input("command> ").strip()
        if inp == "exit":
            break
        parts = inp.split()
        if not parts:
            continue
        op = parts[0]
        if op == "ls":
            system.show_listing()
        elif op == "create":
            if len(parts) == 2:
                system.add_record(parts[1])
            else:
                print("Неправильна команда. Використовуйте: create <назва>")
        elif op == "open":
            if len(parts) == 2:
                system.open_record(parts[1])
            else:
                print("Неправильна команда. Використовуйте: open <назва>")
        elif op == "close":
            if len(parts) == 2:
                try:
                    handle = int(parts[1])
                    system.close_record(handle)
                except ValueError:
                    print("Неправильна команда. Використовуйте: close <номер>")
            else:
                print("Неправильна команда. Використовуйте: close <номер>")
        elif op == "write":
            if len(parts) == 3:
                try:
                    handle = int(parts[1])
                    amount = int(parts[2])
                    system.write_record(handle, amount)
                except ValueError:
                    print("Неправильна команда. Використовуйте: write <номер> <кількість>")
            else:
                print("Неправильна команда. Використовуйте: write <номер> <кількість>")
        elif op == "read":
            if len(parts) == 3:
                try:
                    handle = int(parts[1])
                    amount = int(parts[2])
                    system.read_record(handle, amount)
                except ValueError:
                    print("Неправильна команда. Використовуйте: read <номер> <кількість>")
            else:
                print("Неправильна команда. Використовуйте: read <номер> <кількість>")
        elif op == "seek":
            if len(parts) == 3:
                try:
                    handle = int(parts[1])
                    offset = int(parts[2])
                    system.seek_record(handle, offset)
                except ValueError:
                    print("Неправильна команда. Використовуйте: seek <номер> <зміщення>")
            else:
                print("Неправильна команда. Використовуйте: seek <номер> <зміщення>")
        elif op == "link":
            if len(parts) == 3:
                system.create_link(parts[1], parts[2])
            else:
                print("Неправильна команда. Використовуйте: link <джерело> <ціль>")
        elif op == "unlink":
            if len(parts) == 2:
                system.remove_link(parts[1])
            else:
                print("Неправильна команда. Використовуйте: unlink <назва>")
        elif op == "truncate":
            if len(parts) == 3:
                try:
                    sz = int(parts[2])
                    system.resize_record(parts[1], sz)
                except ValueError:
                    print("Неправильна команда. Використовуйте: truncate <назва> <розмір>")
            else:
                print("Неправильна команда. Використовуйте: truncate <назва> <розмір>")
        elif op == "stat":
            if len(parts) == 2:
                system.show_status(parts[1])
            else:
                print("Неправильна команда. Використовуйте: stat <назва>")
        elif op == "mkdir":
            if len(parts) == 2:
                system.add_folder(parts[1])
            else:
                print("Неправильна команда. Використовуйте: mkdir <ім'я>")
        elif op == "rm":
            if len(parts) == 2:
                system.delete_record(parts[1])
            else:
                print("Неправильна команда. Використовуйте: rm <назва>")
        elif op == "rmdir":
            if len(parts) == 2:
                system.delete_folder(parts[1])
            else:
                print("Неправильна команда. Використовуйте: rmdir <ім'я>")
        else:
            print("Невідома команда:", op)
if __name__ == '__main__':
    start()
