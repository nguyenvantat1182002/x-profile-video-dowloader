import x
import os
import json

from typing import Tuple
from queue import Queue
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, pyqtSignal, QMutex, QMutexLocker, QReadWriteLock


class DownloaderThread(QThread):
    updated_downloaded = pyqtSignal(int, int)

    def __init__(self, usernames: Queue[Tuple[int, str]], max_videos: int, max_thread: int, duration: int):
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
    def duration(self) -> int:
        return self._duration

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
    def username(self) -> Queue[Tuple[int, str]]:
        return self._usernames

    def run(self):
        with open(os.path.join(os.getcwd(), 'config.json'), encoding='utf-8') as file:
            data = json.load(file)
            token = data['token']
            cookie = data['cookie']

        for _ in range(self._max_thread):
            item = DownloaderRunnable(self, token, cookie)
            self._pool.start(item)

            QThread.msleep(300)

        self._pool.waitForDone()


class DownloaderRunnable(QRunnable):
    def __init__(self, parent: DownloaderThread, token: str, cookie: str):
        super().__init__()

        self._parent = parent
        self._token = token
        self._cookie = cookie

    def run(self):
        while not self._parent.stop:
            with QMutexLocker(self._parent.mutex):
                if self._parent.username.empty():
                    break

                row, username = self._parent.username.get_nowait()
            
            api = x.X(self._token, self._cookie)

            try:
                user_id = api.get_rest_id(username)
                print(username, user_id)
                
                if not user_id:
                    self._parent.updated_downloaded.emit(row, -1)
                    continue
                
                output = os.path.join(os.getcwd(), 'output', username)
                if not os.path.exists(output):
                    os.makedirs(output)

                next_items = None
                done = False

                while not done and not self._parent.stop:
                    videos, cursor = api.get_video_urls(user_id, next_items)

                    if not cursor:
                        self._parent.updated_downloaded.emit(row, -1)
                        return
                    
                    for video in videos:
                        print(video.url, video.duration_millis)

                        if self._parent.stop:
                            break

                        if x.milliseconds_to_seconds(video.duration_millis) < self._parent.duration:
                            files = os.listdir(output)
                            total_video = len(files)

                            if total_video > 0:
                                self._parent.updated_downloaded.emit(row, total_video)

                            if total_video >= self._parent.max_video:
                                done = True
                                break

                            file_name = total_video + 1 if not files else total_video
                            x.download_video(video.url, os.path.join(output, f'{file_name}.mp4'))

                    next_items = cursor
            except Exception as ex:
                print(ex)
