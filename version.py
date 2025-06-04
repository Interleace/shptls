# version.py
import os.path
my_file = Path("version.txt")
if my_file.is_file():
    with open(my_file) as f:
        __version__ = f.read().strip()
