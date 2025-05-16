from virtfs.vf_const import VFS_BLOCK_SIZE
class DataUnit:
    def __init__(self):
        self.buffer = bytearray(VFS_BLOCK_SIZE)
    def write_unit(self, in_bytes, in_offset, buf_offset, count):
        self.buffer[buf_offset:buf_offset+count] = in_bytes[in_offset:in_offset+count]
    def read_unit(self, out_bytes, out_offset, buf_offset, count):
        out_bytes[out_offset:out_offset+count] = self.buffer[buf_offset:buf_offset+count]
    def update_unit(self, in_bytes, written, buf_offset, rem_size):
        if buf_offset + written > VFS_BLOCK_SIZE:
            raise ValueError("Insufficient unit capacity.")
        self.write_unit(in_bytes, 0, buf_offset, written)
        return written, VFS_BLOCK_SIZE - (buf_offset + written)
    def fetch_unit(self, out_bytes, read_offset, buf_offset, rem_size):
        self.read_unit(out_bytes, read_offset, buf_offset, rem_size)
