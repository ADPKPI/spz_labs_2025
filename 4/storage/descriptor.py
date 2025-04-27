from storage.config import BLOCK_SIZE
from storage.block import Block
from storage.filetype import FileType
class Descriptor:
    counter = 0
    def __init__(self, ftype: FileType):
        self.id = Descriptor.counter
        Descriptor.counter += 1
        self.ftype = ftype
        self.link_count = 1
        self.file_size = 0
        self.blocks = []
    def __str__(self):
        return (f"ID = {self.id}, Тип = {self.ftype.name}, Посилань = {self.link_count}, Розмір = {self.file_size}, Блоків = {len(self.blocks)}")
    def get_data(self, amount: int, pos: int) -> bytes:
        blk_idx = pos // BLOCK_SIZE
        blk_off = pos % BLOCK_SIZE
        result = bytearray(amount)
        read_tot = 0
        while read_tot < amount:
            rem_in_blk = BLOCK_SIZE - blk_off
            if blk_idx < len(self.blocks) and self.blocks[blk_idx] is not None:
                blk = self.blocks[blk_idx]
            else:
                blk = Block()
            if rem_in_blk >= amount - read_tot:
                blk.get_bytes(result, read_tot, blk_off, amount - read_tot)
                read_tot = amount
            else:
                blk.get_bytes(result, read_tot, blk_off, rem_in_blk)
                read_tot += rem_in_blk
                blk_idx += 1
                blk_off = 0
            if blk_idx >= len(self.blocks):
                break
        return bytes(result)
    def put_data(self, in_data: bytes, pos: int) -> bool:
        if pos + len(in_data) >= len(self.blocks) * BLOCK_SIZE:
            print("Недостатньо простору для даних")
            return False
        write_tot = 0
        blk_idx = pos // BLOCK_SIZE
        blk_off = pos % BLOCK_SIZE
        while write_tot < len(in_data):
            if blk_idx < len(self.blocks) and self.blocks[blk_idx] is not None:
                blk = self.blocks[blk_idx]
            else:
                if blk_idx < len(self.blocks):
                    self.blocks[blk_idx] = Block()
                else:
                    self.blocks.append(Block())
                blk = self.blocks[blk_idx]
            rem_in_blk = BLOCK_SIZE - blk_off
            if rem_in_blk >= len(in_data) - write_tot:
                blk.add_bytes(in_data, write_tot, blk_off, len(in_data) - write_tot)
                write_tot = len(in_data)
            else:
                blk.add_bytes(in_data, write_tot, blk_off, rem_in_blk)
                write_tot += rem_in_blk
                blk_idx += 1
                blk_off = 0
        return True
    def set_size(self, new_size: int):
        req_blocks = (new_size // BLOCK_SIZE) + 1
        if len(self.blocks) < req_blocks:
            self.blocks.extend([None] * (req_blocks - len(self.blocks)))
        elif len(self.blocks) > req_blocks:
            self.blocks = self.blocks[:req_blocks]
        self.file_size = new_size
