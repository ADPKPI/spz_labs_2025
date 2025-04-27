from vfsystem import config
class DataBlock:
    def __init__(self):
        self.data = bytearray(config.BUF_SIZE)
    def write(self, bytes_in, in_off, buf_off, count):
        self.data[buf_off:buf_off+count] = bytes_in[in_off:in_off+count]
    def read(self, bytes_out, out_off, buf_off, count):
        bytes_out[out_off:out_off+count] = self.data[buf_off:buf_off+count]
    def update(self, bytes_in, written, buf_off, rem_size):
        if buf_off + written > config.BUF_SIZE:
            raise ValueError("Недостатньо місця в блоці.")
        self.write(bytes_in, 0, buf_off, written)
        return written, config.BUF_SIZE - (buf_off + written)
    def fetch(self, bytes_out, read_off, buf_off, rem_size):
        self.read(bytes_out, read_off, buf_off, rem_size)
