from queue import Queue
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, pyqtSignal, QMutex, QMutexLocker, QReadWriteLock


class DownloaderThread(QThread):
    updated_downloaded = pyqtSignal(int)

    def __init__(self, usernames: Queue[str], max_videos: int, max_thread: int, duration: int):
        super().__init__()

        self._usernames = usernames
        self._max_videos = max_videos
        self._max_thread = max_thread
        self._duration = duration
        self._mutex =  QMutex()
        self._rw_lock = QReadWriteLock()
        self._stop = False
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(99)

    @property
    def stop(self) -> bool:
        return self._stop
    
    @stop.setter
    def stop(self, value: bool):
        self._stop =  value

    @property
    def rw_lock(self) -> QReadWriteLock:
        return self._rw_lock

    @property
    def mutex(self) -> QMutex:
        return self._mutex

    @property
    def max_video(self) -> int:
        return self._max_videos

    @property
    def username(self) -> Queue[str]:
        return self._usernames

    def run(self):
        for _ in range(self._max_thread):
            item = DownloaderRunnable(self)
            self._pool.start(item)

            QThread.msleep(300)

        self._pool.waitForDone()


class DownloaderRunnable(QRunnable):
    def __init__(self, parent: DownloaderThread):
        super().__init__()

        self._parent = parent

    def run(self):
        while 1:
            with QMutexLocker(self._parent.mutex):
                if self._parent.username.empty():
                    break

                username = self._parent.username.get_nowait()

                print(username)

            QThread.msleep(5000)
            