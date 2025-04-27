import random
import time
from memory_ctrl import MemoryController

class SegmentData:
    def __init__(self):
        self.data_buffer = None
        self.data_length = 0
        self.data_hash = 0

def compute_hash(data, size):
    result = 0
    for i in range(size):
        result = ((result << 3) ^ (result >> 5)) ^ data[i]
    return result

def fill_data(data, size):
    for i in range(size):
        data[i] = random.getrandbits(8)

def alloc_and_fill(size):
    mem = MemoryController.alloc_bytes(size)
    if mem:
        fill_data(mem, size)
    return mem

def check_integrity(pool, amount):
    for item in pool[:amount]:
        if item.data_buffer and compute_hash(item.data_buffer, item.data_length) != item.data_hash:
            print("Перевірка даних не пройшла для [{}]".format(hex(id(item.data_buffer))))
            return False
    return True

def create_segment(entry, verbose, MIN_SIZE, MAX_SIZE):
    lgt = random.randint(MIN_SIZE, MAX_SIZE - 1)
    if verbose:
        print("Виділення об'єму {} ".format(lgt), end="")
    mem = alloc_and_fill(lgt)
    if mem:
        entry.data_length = lgt
        entry.data_buffer = mem
        entry.data_hash = compute_hash(mem, lgt)
        if verbose:
            print("-> [{}]".format(hex(id(mem))))
    else:
        if verbose:
            print("не вдалося")
            
def adjust_segment(entry, verbose, MIN_SIZE, MAX_SIZE):
    if verbose:
        print("Зміна розміру [{}] {} ".format(hex(id(entry.data_buffer)), entry.data_length), end="")
    new_length = random.randint(MIN_SIZE, MAX_SIZE - 1)
    partial = min(new_length, entry.data_length)
    cur_hash = compute_hash(entry.data_buffer, partial)
    updated = MemoryController.change_size(entry.data_buffer, new_length)
    if updated:
        if verbose:
            print("-> [{}] {} ".format(hex(id(updated)), new_length))
        if cur_hash != compute_hash(updated, partial):
            print("Перевірка даних не пройшла для [{}]".format(hex(id(updated))))
            return False
        fill_data(updated, new_length)
        entry.data_buffer = updated
        entry.data_length = new_length
        entry.data_hash = compute_hash(updated, new_length)
    else:
        if verbose:
            print("не вдалося")
    return True

def check_final(pool, amount):
    for item in pool[:amount]:
        if item.data_buffer and compute_hash(item.data_buffer, item.data_length) != item.data_hash:
            print("Фінальна перевірка не пройшла для [{}]".format(hex(id(item.data_buffer))))
            return False
    return True

def free_all(pool, amount):
    for item in pool[:amount]:
        MemoryController.free_bytes(item.data_buffer)

def free_segment(entry, verbose):
    if verbose:
        print("Звільнення [{}]".format(hex(id(entry.data_buffer))))
    MemoryController.free_bytes(entry.data_buffer)
    entry.data_buffer = None

def run_memory_tests(verbose):
    TOTAL = 100
    MIN_SIZE = 1
    MAX_SIZE = 4094 * 10
    ITERATIONS = 1000
    pool = [SegmentData() for _ in range(TOTAL)]
    for _ in range(ITERATIONS):
        if verbose:
            MemoryController.display_status("------------------------")
        if not check_integrity(pool, TOTAL):
            return
        idx = random.randint(0, TOTAL - 1)
        if pool[idx].data_buffer is None:
            create_segment(pool[idx], verbose, MIN_SIZE, MAX_SIZE)
        elif random.getrandbits(1):
            if not adjust_segment(pool[idx], verbose, MIN_SIZE, MAX_SIZE):
                return
        else:
            free_segment(pool[idx], verbose)
    if not check_final(pool, TOTAL):
        return
    free_all(pool, TOTAL)
    if verbose:
        MemoryController.display_status("------------------------")
