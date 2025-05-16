Серед наведених вимог було виокремлено 5, що стосуються символічних посилань. 1-3 були виконані в першій версії роботи, 4-5 доопрацьовано.

1. Символічне ім'я - це тип файлу. Ще є інші типи файлів, наприклад: звичайний файл, директорії, сокет. Символічне ім'я також може мати кілька імен.

2. Терміни "symbolic link" та "hard link" мають слово "link", але перше позначає тип файлу або файл, а друге позначає запис директорії, тобто не тип файлу і не файл.

3. Символічне посилання є файл певного типу. На символічне посилання, як на файл іншого типу можуть посилатися кілька імен. *Лекція 15

`virtfs/file_category.py`
```
from enum import Enum
class FileCategory(Enum):
    REGULAR = 1
    DIRECTORY = 2
    SYMLINK = 3
```

`virtfs/virt_filesys.py`
```
243: def make_symlink(self, link_val, target_path):

...

258:     new_link = VirtualFile(link_name, VirtualFileDesc(FileCategory.SYMLINK))
```

4. Функція яка шукає файл за шляховим ім'ям має бути одна в системі і має мати прапорець, який вказує чи треба йти за символічним посиланням, якщо останній компонент шляхового імені посилається на символічне посилання. Йти за символічним посиланням у цій програмі треба тільки для open(), ls() та cd().

5. Якщо компонент шляхового імені посилається на символічне посилання, то його вміст конкатенуємо з залишком шляхового імені. Якщо результат починається з '/', то шукаємо компоненти починаючи з кореневої директорії, інакше з директорії, де є ім'я, яке посилається на це символічне посилання. Інформація про це є в лекції 15.

- Якщо компонент шляхового імені посилається на символічне посилання, то його вміст конкатенуємо з залишком шляхового імені.

`virtfs/virt_filesys.py`

```
is_last = (i == len(parts) - 1)
if is_last and found.metadata.file_cat == FileCategory.SYMLINK and follow_symlinks:
    raw = found.metadata.retrieve_data(found.metadata.file_size, 0)
    link_target = raw.decode()
    new_path = link_target
```

- Якщо результат починається з '/', то шукаємо компоненти починаючи з кореневої директорії.

`virtfs/virt_filesys.py`

 ```
 if new_path.startswith("/"):
     return self.path_resolver(new_path, follow_symlinks=True)
```

- Інакше з директорії, де є ім'я, яке посилається на це символічне посилання

`virtfs/virt_filesys.py`

```
prev_active = self.active_dir
self.active_dir = found.dir_parent
res = self.path_resolver(new_path, follow_symlinks=True)
self.active_dir = prev_active
return res
```
