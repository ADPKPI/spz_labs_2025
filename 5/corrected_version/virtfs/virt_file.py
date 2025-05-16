from virtfs.vf_descriptor import VirtualFileDesc
class VirtualFile:
    def __init__(self, name, vdesc):
        self.fname = name
        self.metadata = vdesc
