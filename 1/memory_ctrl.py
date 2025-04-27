import random

class MemoryController:
    @staticmethod
    def alloc_bytes(length):
        return bytearray(random.getrandbits(8) for _ in range(length))
    @staticmethod
    def change_size(data, new_length):
        new_data = bytearray(data)
        if len(new_data) < new_length:
            new_data.extend(bytearray(new_length - len(new_data)))
        else:
            new_data = new_data[:new_length]
        return new_data
    @staticmethod
    def free_bytes(data):
        pass
    @staticmethod
    def display_status(msg):
        print(msg)
