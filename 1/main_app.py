import sys
import time
import random
import logging
from memory_ctrl import MemoryController
from memory_checker import run_memory_tests

def init_data(length):
    d = MemoryController.alloc_bytes(length)
    if d is not None:
        for i in range(len(d)):
            d[i] = random.getrandbits(8)
    return d

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    datefmt="%M:%S"
)

def demo_app():
    logger = logging.getLogger(__name__)

    logger.info("Ініціалізація демонстрації керування пам'яттю")
    seg1 = MemoryController.alloc_bytes(60000)

    logger.info("Виділення блоку1 з розміром 60000 байт, адреса: %s", hex(id(seg1)))
    seg2 = MemoryController.alloc_bytes(512)

    logger.info("Виділення блоку2 з розміром 512 байт, адреса: %s", hex(id(seg2)))
    seg3 = MemoryController.alloc_bytes(13000)

    logger.info("Виділення блоку3 з розміром 13000 байт, адреса: %s", hex(id(seg3)))
    seg4 = MemoryController.alloc_bytes(1024)

    logger.info("Виділення блоку4 з розміром 1024 байт, адреса: %s", hex(id(seg4)))
    MemoryController.display_status("Стан пам'яті після первинного розподілу")
    seg1 = MemoryController.change_size(seg1, 100000)

    logger.info("Блок1 збільшено до 100000 байт, нова адреса: %s", hex(id(seg1)))
    MemoryController.display_status("Стан після збільшення блоку1")
    MemoryController.free_bytes(seg1)

    logger.info("Блок1 звільнено")
    MemoryController.display_status("Стан після звільнення блоку1")
    seg4 = MemoryController.change_size(seg4, 512)
    
    logger.info("Блок4 змінено до 512 байт, нова адреса: %s", hex(id(seg4)))
    MemoryController.display_status("Стан після зміни розміру блоку4")

def tests_app():
    random.seed(int(time.time()))
    run_memory_tests(verbose=True)

def usage():
    print("Режими використання:\n\tdemo — демонстрація роботи пам'яті ($ python main_app.py demo)\n\trun - запустити тестування ($ python main_app.py run)")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)
    cmd = sys.argv[1].lower()
    if cmd == 'demo':
        demo_app()
    elif cmd == 'run':
        tests_app()
    else:
        usage()
        sys.exit(1)
