import secrets
from virtfs import vf_const
from virtfs.virt_file import VirtualFile
from virtfs.file_handle import FileHandle
from virtfs.virt_directory import VirtualDirectory
from virtfs.vf_descriptor import VirtualFileDesc
from virtfs.file_category import FileCategory

class VirtualFS:
    def __init__(self):
        self.fd_table = {i: None for i in range(vf_const.VFS_FD_MAX)}
        self.all_items = []
        root_dir = VirtualDirectory.create_dir("/")
        root_dir.set_parent(root_dir)
        self.all_items.append(root_dir)
        self.active_dir = root_dir
        self.temp_dir = self.active_dir
        self.temp_flag = True

    def path_resolver(self, path_str, follow_symlinks=False):
        self.temp_flag = False
        if path_str and "//" not in path_str:
            if path_str == "/":
                return self.all_items[0]

            self.temp_dir = self.active_dir
            if path_str.startswith("/"):
                self.temp_dir = self.all_items[0]
                path_str = path_str[1:]
            elif path_str.startswith("./"):
                path_str = path_str[2:]
            elif path_str.startswith(self.active_dir.fname + "/"):
                path_str = path_str[len(self.active_dir.fname) + 1:]
            elif path_str.startswith("../"):
                self.temp_dir = self.temp_dir.dir_parent
                path_str = path_str[3:]
            elif path_str.strip() == "..":
                return self.temp_dir.dir_parent
            elif "/" not in path_str:
                self.temp_flag = True
                return self.find_by_name(path_str)
            else:
                return None

            parts = path_str.split("/")
            for i, part in enumerate(parts):
                if part == vf_const.VFS_PAR_DIR:
                    self.temp_dir = self.temp_dir.dir_parent
                    continue
                if part == vf_const.VFS_CUR_DIR:
                    continue

                found = None
                for itm in self.temp_dir.dir_children:
                    if itm.fname == part:
                        found = itm
                        break

                if found is None:
                    return None

                is_last = (i == len(parts) - 1)
                if is_last and found.metadata.file_cat == FileCategory.SYMLINK and follow_symlinks:
                    raw = found.metadata.retrieve_data(found.metadata.file_size, 0)
                    link_target = raw.decode()
                    new_path = link_target
                    if new_path.startswith("/"):
                        return self.path_resolver(new_path, follow_symlinks=True)
                    prev_active = self.active_dir
                    self.active_dir = found.dir_parent
                    res = self.path_resolver(new_path, follow_symlinks=True)
                    self.active_dir = prev_active
                    return res

                if is_last:
                    self.temp_flag = True
                    return found
                if found.metadata.file_cat == FileCategory.DIRECTORY:
                    self.temp_dir = found
                else:
                    return None
        return None

    def status_report(self, path_str):
        print("Статус для " + path_str + ":")
        entry = self.path_resolver(path_str, follow_symlinks=False)
        if entry:
            print(str(entry.metadata))
        else:
            print("Запис не знайдено.")

    def list_directory(self, path_str=None):
        target = self.active_dir
        if path_str:
            entry = self.path_resolver(path_str, follow_symlinks=True)
            if entry and entry.metadata.file_cat == FileCategory.DIRECTORY:
                target = entry
            else:
                print("Невірний шлях або не каталог")
                return
        print("Вміст каталогу:")
        for itm in target.dir_children:
            print(f"{itm.fname}\t=> {itm.metadata.file_cat}, {itm.metadata.desc_id}")

    def make_file(self, path_str):
        print("Створення файлу: " + path_str)
        if not path_str:
            print("Невірний шлях")
            return
        parts = path_str.split("/")
        last_part = parts[-1]
        if not self.validate_name(last_part):
            return
        entry = self.path_resolver(path_str, follow_symlinks=False)
        if entry:
            print("Файл вже існує")
        elif self.temp_flag:
            new_file = VirtualFile(last_part, VirtualFileDesc(FileCategory.REGULAR))
            self.all_items.append(new_file)
            self.temp_dir.append_child(new_file)
            self.temp_dir.metadata.link_count += 1
        else:
            print("Невірний шлях")

    def open_item(self, path_str):
        print("Відкриття: " + path_str)
        entry = self.path_resolver(path_str, follow_symlinks=True)
        if entry is None:
            print("Запис відсутній")
        elif entry.metadata.file_cat == FileCategory.REGULAR:
            fd = self.available_fd()
            if fd != -1:
                self.fd_table[fd] = FileHandle(entry)
                print("Призначено FD: " + str(fd))
            else:
                print("Досягнуто ліміт відкритих файлів")
        else:
            print("Запис є каталогом")

    def close_item(self, fd):
        print("Закриття FD: " + str(fd))
        if self.fd_table.get(fd) is None:
            print("Дескриптор не знайдено")
        else:
            self.fd_table[fd] = None

    def move_offset(self, fd, off_val):
        print("Зсув позиції FD " + str(fd) + " на " + str(off_val))
        hndl = self.fd_table.get(fd)
        if not hndl:
            print("Дескриптор не знайдено")
        elif hndl.file_obj.metadata.file_size <= off_val:
            print("Зсув перевищує розмір файлу")
        else:
            hndl.pos_offset += off_val

    def read_data(self, fd, length):
        print("Читання " + str(length) + " байт з FD " + str(fd))
        hndl = self.fd_table.get(fd)
        if not hndl:
            print("Дескриптор не знайдено")
        else:
            chunk = hndl.file_obj.metadata.retrieve_data(length, hndl.pos_offset)
            hndl.pos_offset += length
            print(list(chunk))

    def write_data(self, fd, length):
        print("Запис " + str(length) + " байт до FD " + str(fd))
        hndl = self.fd_table.get(fd)
        if hndl and hndl.file_obj.metadata.store_data(self.random_bytes(length), hndl.pos_offset):
            hndl.pos_offset += length

    def make_hardlink(self, src_path, dst_path):
        print("Створення жорсткого посилання з " + src_path + " до " + dst_path)
        if not src_path or not dst_path:
            print("Невірний шлях")
            return
        parts = dst_path.split("/")
        dst_name = parts[-1]
        if not self.validate_name(dst_name):
            return
        entry = self.path_resolver(src_path, follow_symlinks=False)
        if not entry or entry.metadata.file_cat != FileCategory.REGULAR:
            print("Джерело не знайдено або не файл")
            return
        if self.path_resolver(dst_path, follow_symlinks=False):
            print("Ціль вже існує")
        elif self.temp_flag:
            new_link = VirtualFile(dst_name, entry.metadata)
            self.all_items.append(new_link)
            entry.metadata.link_count += 1
            self.temp_dir.append_child(new_link)
            self.temp_dir.metadata.link_count += 1
        else:
            print("Невірний шлях")

    def delete_hardlink(self, path_str):
        print("Видалення посилання: " + path_str)
        entry = self.path_resolver(path_str, follow_symlinks=False)
        if not entry or entry.metadata.file_cat != FileCategory.REGULAR:
            print("Запис не знайдено або не файл")
        elif self.temp_flag:
            entry.metadata.link_count -= 1
            self.all_items.remove(entry)
            self.temp_dir.delete_child(entry)
            self.temp_dir.metadata.link_count -= 1
        else:
            print("Невірний шлях")

    def resize_item(self, path_str, new_len):
        print("Зміна розміру " + path_str + " на " + str(new_len))
        entry = self.path_resolver(path_str, follow_symlinks=False)
        if not entry:
            print("Запис не знайдено")
        elif entry.metadata.file_cat == FileCategory.REGULAR:
            entry.metadata.adjust_size(new_len)
        else:
            print("Запис є каталогом")

    def make_directory(self, path_str):
        print("Створення каталогу: " + path_str)
        if not path_str:
            print("Невірний шлях")
            return
        parts = path_str.split("/")
        dir_name = parts[-1]
        if not self.validate_name(dir_name):
            return
        if self.path_resolver(path_str, follow_symlinks=False):
            print("Запис вже існує")
        elif self.temp_flag:
            new_dir = VirtualDirectory.create_dir(dir_name)
            self.all_items.append(new_dir)
            new_dir.set_parent(self.temp_dir)
            self.temp_dir.append_child(new_dir)
            self.temp_dir.metadata.link_count += 1
        else:
            print("Невірний шлях")

    def delete_directory(self, path_str):
        print("Видалення каталогу: " + path_str)
        entry = self.path_resolver(path_str, follow_symlinks=False)
        if not entry:
            print("Запис не знайдено")
        elif entry.metadata.file_cat == FileCategory.DIRECTORY:
            if not entry.dir_children:
                entry.dir_parent.delete_child(entry)
                self.all_items.remove(entry)
            else:
                print("Каталог не порожній")
        else:
            print("Запис є файлом")

    def switch_directory(self, path_str):
        print("Перехід до каталогу: " + path_str)
        entry = self.path_resolver(path_str, follow_symlinks=True)
        if entry and entry.metadata.file_cat == FileCategory.DIRECTORY:
            self.active_dir = entry
        else:
            print("Невірний шлях або не каталог")

    def current_location(self):
        print("Поточний каталог:")
        print(self.active_dir.fname)

    def make_symlink(self, link_val, target_path):
        print(f"Створення символічного посилання: {link_val} на {target_path}")
        if not target_path or len(link_val.encode()) > vf_const.VFS_BLOCK_SIZE:
            print("Невірний шлях або розмір лінка перевищено")
            return
        parts = target_path.split("/")
        link_name = parts[-1]
        if not self.validate_name(link_name):
            return
        if self.path_resolver(target_path, follow_symlinks=False):
            print("Запис вже існує")
        elif self.temp_flag:
            new_link = VirtualFile(link_name, VirtualFileDesc(FileCategory.SYMLINK))
            new_link.metadata.adjust_size(vf_const.VFS_BLOCK_SIZE - 1)
            new_link.metadata.store_data(link_val.encode(), 0)
            self.all_items.append(new_link)
            self.temp_dir.append_child(new_link)
            self.temp_dir.metadata.link_count += 1
        else:
            print("Невірний шлях")

    def find_by_name(self, name_str):
        for itm in self.active_dir.dir_children:
            if itm.fname == name_str:
                return itm
        return None

    def available_fd(self):
        for key, value in self.fd_table.items():
            if value is None:
                return key
        return -1

    def random_bytes(self, length):
        return bytearray(secrets.token_bytes(length))

    def validate_name(self, name_str):
        if len(name_str) < 1 or len(name_str) > vf_const.VFS_NAME_MAX:
            print(name_str + " не відповідає критеріям іменування!")
            return False
        return True

