from vfsystem.file_module import BaseEntry
from vfsystem.descriptor_module import EntryDescriptor
from vfsystem.filetype_enum import FileType
class DirContainer(BaseEntry):
    def __init__(self, name_dir, descriptor):
        super().__init__(name_dir, descriptor)
        self.parent_dir = None
        self.entries = []
    @classmethod
    def new_dir(cls, name_dir):
        desc = EntryDescriptor(FileType.DIRECTORY)
        return cls(name_dir, desc)
    def get_parent(self):
        return self.parent_dir
    def set_parent(self, parent_obj):
        self.parent_dir = parent_obj
    def get_entries(self):
        return self.entries
    def add_entry(self, entry_obj):
        self.entries.append(entry_obj)
        self.info.links += 1
    def remove_entry(self, entry_obj):
        self.entries.remove(entry_obj)
        self.info.links -= 1
