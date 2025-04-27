import random
from storage.config import BLOCK_SIZE, MAX_NAME_LEN, MAX_OPEN_HANDLES
from storage.record import Record
from storage.descriptor import Descriptor
from storage.filetype import FileType
from storage.file_handle import FileHandle
class StorageSystem:
    def __init__(self):
        self.open_files = {i: None for i in range(MAX_OPEN_HANDLES)}
        self.records = []
        self.folders = []
    def show_status(self, name: str):
        rec = self._find_record(name)
        fol = self._find_folder(name)
        if rec:
            print(rec.desc)
        elif fol:
            print(fol.desc)
        else:
            print("Запис не знайдено")
    def delete_record(self, name: str):
        rec = self._find_record(name)
        if rec:
            self.records.remove(rec)
        else:
            print("Запис не знайдено")
    def delete_folder(self, name: str):
        fol = self._find_folder(name)
        if fol:
            self.folders.remove(fol)
        else:
            print("Папку не знайдено")
    def show_listing(self):
        for rec in self.records:
            print(f"{rec.name}\t => {rec.desc.ftype.name}, {rec.desc.id}")
        for fol in self.folders:
            print(f"{fol.name}\t => {fol.desc.ftype.name}, {fol.desc.id}")
    def add_record(self, name: str):
        if self._check_filename_length(name):
            if self._find_record(name) or self._find_folder(name):
                print("Запис з такою назвою вже існує")
            else:
                new_rec = Record(name, Descriptor(FileType.NORMAL))
                self.records.append(new_rec)
    def add_folder(self, name: str):
        if self._check_filename_length(name):
            if self._find_record(name) or self._find_folder(name):
                print("Запис з такою назвою вже існує")
            else:
                new_fol = Record(name, Descriptor(FileType.FOLDER))
                self.folders.append(new_fol)
    def open_record(self, name: str):
        rec = self._find_record(name)
        if not rec:
            print("Запис не знайдено")
        else:
            hndl = self._next_free_handle()
            if hndl != -1:
                self.open_files[hndl] = FileHandle(rec)
                print("Номер дескриптора =", hndl)
            else:
                print("Дійшли до ліміту відкритих записів")
    def close_record(self, handle: int):
        if self.open_files.get(handle) is None:
            print("Запис не знайдено")
        else:
            self.open_files[handle] = None
    def seek_record(self, handle: int, offset: int):
        fh = self.open_files.get(handle)
        if fh is None:
            print("Запис не знайдено")
        else:
            if fh.rec.desc.file_size <= offset:
                print("Зміщення за межами розміру")
            else:
                fh.pos += offset
    def read_record(self, handle: int, amount: int):
        fh = self.open_files.get(handle)
        if fh is None:
            print("Запис не знайдено")
        else:
            data = fh.rec.desc.get_data(amount, fh.pos)
            fh.pos += amount
            print(list(data))
    def write_record(self, handle: int, amount: int):
        fh = self.open_files.get(handle)
        if fh is None:
            print("Запис не знайдено")
        else:
            bts = self._gen_random_bytes(amount)
            if fh.rec.desc.put_data(bts, fh.pos):
                fh.pos += amount
    def create_link(self, source: str, target: str):
        if self._check_filename_length(target):
            src = self._find_record(source)
            if not src:
                print(f"Запис {source} відсутній")
            else:
                if self._find_record(target):
                    print(f"Запис {target} вже існує")
                else:
                    self.records.append(Record(target, src.desc))
                    src.desc.link_count += 1
    def remove_link(self, name: str):
        rec = self._find_record(name)
        if not rec:
            print(f"Запис {name} відсутній")
        else:
            rec.desc.link_count -= 1
            self.records.remove(rec)
    def resize_record(self, name: str, new_size: int):
        rec = self._find_record(name)
        if not rec:
            print(f"Запис {name} відсутній")
        else:
            rec.desc.set_size(new_size)
    def _find_record(self, name: str):
        for rec in self.records:
            if rec.name == name:
                return rec
        return None
    def _find_folder(self, name: str):
        for fol in self.folders:
            if fol.name == name:
                return fol
        return None
    def _next_free_handle(self) -> int:
        for i in range(MAX_OPEN_HANDLES):
            if self.open_files[i] is None:
                return i
        return -1
    def _gen_random_bytes(self, size: int) -> bytes:
        return bytes(random.getrandbits(8) for _ in range(size))
    def _check_filename_length(self, name: str) -> bool:
        return 1 <= len(name) <= MAX_NAME_LEN
