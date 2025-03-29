import re
import os

TAKE_NAME = lambda: re.search(r'^\w+', os.getlogin()).group()