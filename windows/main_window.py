import os
import x

from queue import Queue
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
from .threads import DownloaderThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.getcwd(), 'ui', 'MainWindow.ui'), self)
        
        self.pushButton.clicked.connect(self.pushButton_click)
        self.pushButton_2.clicked.connect(self.pushButton_2_click)
        self.pushButton_3.clicked.connect(self.pushButton_3_click)

        self._dowloader = None

    def pushButton_2_click(self):
        match self.pushButton_2.text():
            case 'Bắt đầu':
                self.pushButton_2.setText('Dừng')

                self._dowloader = DownloaderThread(
                    usernames=self._get_usernames_queue(),
                    max_videos=self.spinBox.value(),
                    max_thread=self.spinBox_3.value(),
                    duration=self.spinBox_2.value()
                )
                self._dowloader.finished.connect(self._task_finished)
                self._dowloader.start()
            case 'Dừng':
                self.pushButton_2.setText('Dừng...')
                self._dowloader.stop = True

    def pushButton_3_click(self):
        os.startfile(os.path.join(os.getcwd(), 'output'))

    def pushButton_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self, directory='.', filter='Text Document (*.txt)')
        if not file_path:
            return
        
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)

        with open(file_path, encoding='utf-8') as file:
            lines = file.read().splitlines()

        for line in lines:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(x.get_username_from_url(line)))

        self.label.setText(f'Profile links: {self.tableWidget.rowCount()}')
        self.lineEdit.setText(file_path)

    def _task_finished(self):
        QMessageBox.information(self, 'Thông báo', 'Đã dừng' if self._dowloader.stop else 'Hoàn thành')
        self.pushButton_2.setText('Bắt đầu')
        self._dowloader = None

    def _get_usernames_queue(self):
        q = Queue()
        for row in range(self.tableWidget.rowCount()):
            username = self.tableWidget.item(row, 0).text()
            q.put_nowait(username)
        return q
    