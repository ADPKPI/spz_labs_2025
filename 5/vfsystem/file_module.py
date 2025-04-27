from vfsystem.descriptor_module import EntryDescriptor
class BaseEntry:
    def __init__(self, entry_name, descriptor):
        self.entry_name = entry_name
        self.info = descriptor
