# pyi_cwd_hook.py

import os, sys

# If we’re running in a PyInstaller bundle, switch CWD to the temp folder
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)