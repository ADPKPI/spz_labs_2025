### Переніс реалізацію з Python на C:  

Відмовився від `bytearray`-моделей і класів (`DataBlock`, `BalancedTree`), натомість у файлі `block.c` визначено `struct Block` із полями `size`, `is_free`, `prev`/`next` та виділено окремі модулі для алокатора (`allocator.c`) і керування пам’яттю (`kernel.c`).  

---

### Додав активне використання покажчиків, арифметики покажчиків і приведення типів

---

### Реалізував усі ключові структури та алгоритми у вигляді C-модулів, а не обгорток на Python:  
  — `block.c` з логікою сортування та злиття сусідніх фрагментів;  
  — `avl/avl.c` із `struct AVLNode`, функціями `avl_insert`/`avl_remove`/`avl_balance`;  
  — `kernel.c`/`kernel.h` із функціями `kernel_memory_allocate` (на Linux через `mmap`, на Windows — `VirtualAlloc`), `kernel_memory_free` і `kernel_memory_reset` (з `madvise` або `MEM_RESET`);  
  — `tester.c` замість Python-скрипта: генерація випадкових сценаріїв `allocate`/`realloc`/`free`, перевірка контрольних сум та вивід результатів через `printf`.  
