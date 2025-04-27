import mmap

def get_pages(length):
    return mmap.mmap(-1, length)

def return_pages(obj, length):
    obj.close()

def reset_area(obj, length):
    if isinstance(obj, bytearray):
        for i in range(length):
            obj[i] = 0x7e
    elif hasattr(obj, 'seek') and hasattr(obj, 'write'):
        obj.seek(0)
        obj.write(b'\x7e' * length)
