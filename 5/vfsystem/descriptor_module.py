from vfsystem import config
from vfsystem.block_module import DataBlock
from vfsystem.filetype_enum import FileType
class EntryDescriptor:
    count_id = 0
    ZERO_BLOCK = DataBlock()
    def __init__(self, ftype):
        self.ident = EntryDescriptor.count_id
        EntryDescriptor.count_id += 1
        self.ftype = ftype
        self.links = 1
        self.size = 0
        self.blocks = []
    def __str__(self):
        return "Ідентифікатор=" + str(self.ident) + ", Тип=" + str(self.ftype) + ", Зв'язків=" + str(self.links) + ", Розмір=" + str(self.size) + ", Блоків=" + str(len(self.blocks))
    def get_data(self, length, offset):
        blk_index = offset // config.BUF_SIZE
        blk_offset = offset % config.BUF_SIZE
        res = bytearray(length)
        collected = 0
        while collected < length:
            remain = config.BUF_SIZE - blk_offset
            current_blk = self.blocks[blk_index] if blk_index < len(self.blocks) and self.blocks[blk_index] is not None else EntryDescriptor.ZERO_BLOCK
            if remain >= length - collected:
                current_blk.fetch(res, collected, blk_offset, length - collected)
                collected = length
            else:
                current_blk.fetch(res, collected, blk_offset, remain)
                collected += remain
                blk_index += 1
                blk_offset = 0
            if blk_index >= len(self.blocks):
                break
        return res
    def put_data(self, input_bytes, offset):
        if offset + len(input_bytes) >= len(self.blocks) * config.BUF_SIZE:
            print("Недостатньо місця.")
            return False
        stored = 0
        blk_index = offset // config.BUF_SIZE
        blk_offset = offset % config.BUF_SIZE
        while stored < len(input_bytes):
            if blk_index >= len(self.blocks):
                break
            current_blk = self.blocks[blk_index]
            if current_blk is None:
                from vfsystem.block_module import DataBlock
                self.blocks[blk_index] = DataBlock()
                current_blk = self.blocks[blk_index]
            rem = config.BUF_SIZE - blk_offset
            if rem >= len(input_bytes) - stored:
                current_blk.update(input_bytes, len(input_bytes) - stored, blk_offset, len(input_bytes) - stored)
                stored = len(input_bytes)
            else:
                current_blk.update(input_bytes, rem, buf_off=blk_offset, rem_size=rem)
                stored += rem
                blk_index += 1
                blk_offset = 0
        return True
    def resize(self, new_size):
        new_blk = new_size // config.BUF_SIZE + 1
        if len(self.blocks) < new_blk:
            self.blocks.extend([None]*(new_blk - len(self.blocks)))
        elif len(self.blocks) > new_blk:
            self.blocks = self.blocks[:new_blk]
        self.size = new_size
