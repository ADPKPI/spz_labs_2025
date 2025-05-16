from virtfs.virt_file import VirtualFile
from virtfs.vf_descriptor import VirtualFileDesc
from virtfs.file_category import FileCategory
class VirtualDirectory(VirtualFile):
    def __init__(self, d_name, vdesc):
        super().__init__(d_name, vdesc)
        self.dir_parent = None
        self.dir_children = []
    @classmethod
    def create_dir(cls, d_name):
        desc = VirtualFileDesc(FileCategory.DIRECTORY)
        return cls(d_name, desc)
    def set_parent(self, parent_obj):
        self.dir_parent = parent_obj
    def list_children(self):
        return self.dir_children
    def append_child(self, child_obj):
        self.dir_children.append(child_obj)
        self.metadata.link_count += 1
    def delete_child(self, child_obj):
        self.dir_children.remove(child_obj)
        self.metadata.link_count -= 1
