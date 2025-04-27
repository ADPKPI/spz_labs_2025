import secrets
from vfsystem import config
from vfsystem.file_module import BaseEntry
from vfsystem.file_handle import FileHandle
from vfsystem.dir_module import DirContainer
from vfsystem.descriptor_module import EntryDescriptor
from vfsystem.filetype_enum import FileType
class VirtFS:
    def __init__(self):
        self.fd_map = {i: None for i in range(config.MAX_FD)}
        self.entries = []
        root = DirContainer.new_dir("/")
        root.set_parent(root)
        self.entries.append(root)
        self.current_dir = root
        self.temp_dir = self.current_dir
        self.temp_flag = True
    def get_path_entry(self, path_str):
        self.temp_flag = False
        if path_str and "//" not in path_str:
            if path_str == "/":
                return self.entries[0]
            self.temp_dir = self.current_dir
            if path_str.startswith("/"):
                self.temp_dir = self.entries[0]
                path_str = path_str[1:]
            elif path_str.startswith("./"):
                path_str = path_str[2:]
            elif path_str.startswith(self.current_dir.entry_name + "/"):
                path_str = path_str[len(self.current_dir.entry_name)+1:]
            elif path_str.startswith("../"):
                self.temp_dir = self.temp_dir.parent_dir
                path_str = path_str[3:]
            elif path_str.strip() == "..":
                return self.temp_dir.parent_dir
            elif "/" not in path_str:
                self.temp_flag = True
                return self.find_entry(path_str)
            else:
                return None
            parts = path_str.split("/")
            for i, seg in enumerate(parts):
                if seg == config.DOT_DOT:
                    self.temp_dir = self.temp_dir.parent_dir
                elif seg != config.DOT:
                    found = None
                    for item in self.temp_dir.entries:
                        if seg == item.entry_name:
                            found = item
                            break
                    if i == len(parts) - 1:
                        self.temp_flag = True
                        return found
                    else:
                        if found and found.info.ftype == FileType.DIRECTORY:
                            self.temp_dir = found
                        else:
                            return None
        return None
    def show_status(self, path_str):
        print("Статус для " + path_str + ":")
        entry = self.get_path_entry(path_str)
        if entry:
            print(str(entry.info))
        else:
            print("Запис не знайдено!")
    def list_dir(self):
        print("Перелік записів:")
        for item in self.current_dir.entries:
            print(f"{item.entry_name}\t=> {item.info.ftype}, {item.info.ident}")
    def add_file(self, path_str):
        print("Додавання файлу: " + path_str)
        if not path_str:
            print("Невірний шлях")
        else:
            parts = path_str.split("/")
            name_part = parts[-1]
            if self.valid_name(name_part):
                entry = self.get_path_entry(path_str)
                if entry:
                    print("Файл уже існує")
                else:
                    if self.temp_flag:
                        new_file = BaseEntry(name_part, EntryDescriptor(FileType.REGULAR))
                        self.entries.append(new_file)
                        self.temp_dir.add_entry(new_file)
                        self.temp_dir.info.links += 1
                    else:
                        print("Невірний шлях")
    def open_file(self, path_str):
        print("Відкриття: " + path_str)
        entry = self.get_path_entry(path_str)
        if entry is None:
            print("Запис відсутній")
        else:
            if entry.info.ftype == FileType.REGULAR:
                fd = self.next_fd()
                if fd != -1:
                    self.fd_map[fd] = FileHandle(entry)
                    print("Призначено FD = " + str(fd))
                else:
                    print("Досягнуто ліміту відкритих файлів")
            else:
                print("Запис є директорією")
    def close_file(self, fd):
        print("Закриття FD " + str(fd))
        handle = self.fd_map.get(fd)
        if handle is None:
            print("Обробник не знайдено")
        else:
            self.fd_map[fd] = None
    def update_offset(self, fd, offset_val):
        print("Зміна позиції FD " + str(fd) + " на " + str(offset_val))
        handle = self.fd_map.get(fd)
        if handle is None:
            print("Обробник не знайдено")
        else:
            if handle.ref.info.size <= offset_val:
                print("Зміщення виходить за розмір")
            else:
                handle.pos += offset_val
    def read_file(self, fd, length):
        print("Читання " + str(length) + " байт з FD " + str(fd))
        handle = self.fd_map.get(fd)
        if handle is None:
            print("Обробник не знайдено")
        else:
            chunk = handle.ref.info.get_data(length, handle.pos)
            handle.pos += length
            print(list(chunk))
    def write_file(self, fd, length):
        print("Запис " + str(length) + " байт до FD " + str(fd))
        handle = self.fd_map.get(fd)
        if handle is None:
            print("Обробник не знайдено")
        else:
            if handle.ref.info.put_data(self.generate_bytes(length), handle.pos):
                handle.pos += length
    def add_link(self, source_path, dest_path):
        print("Створення жорсткого посилання від " + source_path + " до " + dest_path)
        if not source_path:
            print("Невірний вихідний шлях")
        elif not dest_path:
            print("Невірний цільовий шлях")
        else:
            parts_src = source_path.split("/")
            src_name = parts_src[-1]
            parts_dest = dest_path.split("/")
            dest_name = parts_dest[-1]
            if self.valid_name(dest_name):
                entry = self.get_path_entry(source_path)
                if entry is None:
                    print("Вихідний файл " + src_name + " не знайдено")
                else:
                    if entry.info.ftype == FileType.REGULAR:
                        entry2 = self.get_path_entry(dest_path)
                        if entry2 is not None:
                            print("Цільовий файл " + dest_name + " уже існує")
                        else:
                            if self.temp_flag:
                                new_link = BaseEntry(dest_name, entry.info)
                                self.entries.append(new_link)
                                entry.info.links += 1
                                self.temp_dir.add_entry(new_link)
                                self.temp_dir.info.links += 1
                            else:
                                print("Невірний шлях")
                    else:
                        print("Запис вихідного — директорія")
    def del_link(self, path_str):
        print("Видалення посилання для " + path_str)
        entry = self.get_path_entry(path_str)
        if entry is None:
            print("Запис " + path_str + " не знайдено")
        else:
            if entry.info.ftype == FileType.REGULAR:
                if self.temp_flag:
                    entry.info.links -= 1
                    self.entries.remove(entry)
                    self.temp_dir.remove_entry(entry)
                    self.temp_dir.info.links -= 1
                else:
                    print("Невірний шлях")
            else:
                print("Запис є директорією")
    def set_size(self, path_str, new_len):
        print("Зміна розміру для " + path_str + " на " + str(new_len))
        entry = self.get_path_entry(path_str)
        if entry is None:
            print("Запис " + path_str + " не знайдено")
        else:
            if entry.info.ftype == FileType.REGULAR:
                entry.info.resize(new_len)
            else:
                print("Запис є директорією")
    def add_directory(self, path_str):
        print("Створення директорії: " + path_str)
        if not path_str:
            print("Невірний шлях")
        else:
            parts = path_str.split("/")
            dir_name = parts[-1]
            if self.valid_name(dir_name):
                existing = self.get_path_entry(path_str)
                if existing is not None:
                    print("Запис уже існує")
                else:
                    if self.temp_flag:
                        new_dir = DirContainer.new_dir(dir_name)
                        self.entries.append(new_dir)
                        new_dir.set_parent(self.temp_dir)
                        self.temp_dir.add_entry(new_dir)
                        self.temp_dir.info.links += 1
                    else:
                        print("Невірний шлях")
    def del_directory(self, path_str):
        print("Видалення директорії: " + path_str)
        entry = self.get_path_entry(path_str)
        if entry is None:
            print("Запис " + path_str + " не знайдено")
        else:
            if entry.info.ftype == FileType.DIRECTORY:
                if len(entry.entries) == 0:
                    entry.parent_dir.remove_entry(entry)
                    self.entries.remove(entry)
                else:
                    print("Директорія не порожня")
            else:
                print("Запис є файлом")
    def cd(self, path_str):
        print("Зміна директорії на " + path_str)
        entry = self.get_path_entry(path_str)
        if entry:
            if entry.info.ftype == FileType.DIRECTORY:
                self.current_dir = entry
            else:
                print("Запис є файлом")
        else:
            print("Невірний шлях")
    def cur_path(self):
        print("Поточна директорія:")
        print(self.current_dir.entry_name)
    def add_symlink(self, link_str, target_path):
        print("Створення символьного посилання " + link_str + " на " + target_path)
        if not target_path:
            print("Невірний цільовий шлях")
        elif len(link_str.encode()) > config.BUF_SIZE:
            print("Рядок посилання занадто довгий")
        else:
            parts = target_path.split("/")
            link_name = parts[-1]
            if self.valid_name(link_name):
                existing = self.get_path_entry(target_path)
                if existing is not None:
                    print("Запис уже існує")
                else:
                    if self.temp_flag:
                        new_link = BaseEntry(link_name, EntryDescriptor(FileType.SYMLINK))
                        new_link.info.resize(config.BUF_SIZE - 1)
                        new_link.info.put_data(link_str.encode(), 0)
                        self.entries.append(new_link)
                        self.temp_dir.add_entry(new_link)
                        self.temp_dir.info.links += 1
                    else:
                        print("Невірний шлях")
    def find_entry(self, name_str):
        for item in self.current_dir.entries:
            if item.entry_name == name_str:
                return item
        return None
    def next_fd(self):
        for k, v in self.fd_map.items():
            if v is None:
                return k
        return -1
    def generate_bytes(self, length):
        return bytearray(secrets.token_bytes(length))
    def valid_name(self, name_str):
        if len(name_str) < 1 or len(name_str) > config.MAX_NAME_LEN:
            print(name_str + " не відповідає вимогам")
            return False
        return True
