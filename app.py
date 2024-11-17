import os

from windows import MainWindow
from PyQt5.QtWidgets import QApplication


folders = ['output']
for folder in folders:
    path = os.path.join(os.getcwd(), folder)
    if not os.path.exists(path):
        os.makedirs(path)


app = QApplication([])

win = MainWindow()
win.show()

app.exec_()
