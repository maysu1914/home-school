from app.app import HomeSchool
import os

if __name__ == '__main__':
    os.add_dll_directory(os.getcwd())  # Python 3.8
    hs = HomeSchool("resources/ders-programi.json")
    hs.run()
