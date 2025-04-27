from storage.config import BLOCK_SIZE
class Block:
    def __init__(self):
        self.bytes_data = bytearray(BLOCK_SIZE)
    def add_bytes(self, in_data: bytes, in_off: int, blk_off: int, length: int):
        self.bytes_data[blk_off:blk_off+length] = in_data[in_off:in_off+length]
    def get_bytes(self, out_data: bytearray, out_off: int, blk_off: int, length: int):
        out_data[out_off:out_off+length] = self.bytes_data[blk_off:blk_off+length]
