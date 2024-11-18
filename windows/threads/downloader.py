import x
import os
import json
import secrets

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Tuple
from queue import Queue
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, pyqtSignal, QMutex, QMutexLocker


@dataclass
class Config:
    token: str
    cookie: str
    time_to_wait_for_next_videos: int = field(default=15)
    max_page: int = field(default=300)
    proxy: str = field(default=None)

    @classmethod
    def load(cls) -> 'Config':
        with open(os.path.join(os.getcwd(), 'config.json'), encoding='utf-8') as file:
            return cls(**json.load(file))


class DownloaderThread(QThread):
    status_updated = pyqtSignal(int, str)

    def __init__(self, usernames: Queue[Tuple[int, str]], max_videos: int, max_thread: int, duration: int):
        super().__init__()

        self._usernames = usernames
        self._max_videos = max_videos
        self._max_thread = max_thread
        self._duration = duration
        self._mutex =  QMutex()
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
    def mutex(self) -> QMutex:
        return self._mutex

    @property
    def max_video(self) -> int:
        return self._max_videos

    @property
    def username(self) -> Queue[Tuple[int, str]]:
        return self._usernames

    def run(self):
        config = Config.load()

        for _ in range(self._max_thread):
            item = DownloaderRunnable(self, config)
            self._pool.start(item)

            QThread.msleep(300)

        self._pool.waitForDone()


class DownloaderRunnable(QRunnable):
    def __init__(self, parent: DownloaderThread, config: Config):
        super().__init__()

        self._parent = parent
        self._config = config

    def run(self):
        while not self._parent.stop:
            with QMutexLocker(self._parent.mutex):
                if self._parent.username.empty():
                    break

                row, username = self._parent.username.get_nowait()
            
            api = x.X(self._config.token, self._config.cookie, self._config.proxy)

            try:
                with QMutexLocker(self._parent.mutex):
                    user_id = api.get_rest_id(username)

                print(username, user_id)
                
                if not user_id:
                    self._parent.status_updated.emit(row, 'Không thể lấy user_id')
                    continue
                
                output = os.path.join(os.getcwd(), 'output', username)
                if not os.path.exists(output):
                    os.makedirs(output)

                next_items = None
                done = False
                current_page = 0

                while not done and not self._parent.stop:
                    if current_page >= self._config.max_page:
                        total_video = self._get_total_video(output)
                        if total_video < 1:
                            self._parent.status_updated.emit(row, 'Không tìm thấy videos nào của người dùng này')
                        break

                    with QMutexLocker(self._parent.mutex):
                        videos, cursor = api.get_video_urls(user_id, next_items)

                    if not cursor:
                        self._parent.status_updated.emit(row, 'Không thể lấy videos')
                        break
                    
                    for video in videos:
                        if self._parent.stop:
                            break
                        
                        duration = x.milliseconds_to_seconds(video.duration_millis)
                        print(video.url, duration, duration < self._parent.duration)

                        if duration < self._parent.duration:
                            total_video = self._get_total_video(output)

                            if total_video > 0:
                                self._parent.status_updated.emit(row, f'Đã tải được {total_video} videos')

                            if total_video >= self._parent.max_video:
                                done = True
                                break

                            x.download_video(video.url, os.path.join(output, f'{secrets.token_hex(6)}.mp4'))

                    current_page += 20

                    if not done:
                        next_items = cursor

                        end_time = datetime.now() + timedelta(seconds=self._config.time_to_wait_for_next_videos)
                        total_video = self._get_total_video(output)
                        while not self._parent.stop:
                            if datetime.now() > end_time:
                                break
                            
                            remaining_time = end_time - datetime.now()
                            message = f'Đã tải được {total_video} videos. Sẽ tiếp tục sau {int(remaining_time.total_seconds())}'
                            if total_video < 1:
                                message = f'Sẽ tiếp tục sau {int(remaining_time.total_seconds())}'
                            self._parent.status_updated.emit(row, message)

                            QThread.msleep(1000)

                total_video = self._get_total_video(output)
                if total_video > 0:
                    self._parent.status_updated.emit(row, f'Đã tải được {total_video} videos')
            except Exception as ex:
                print(ex)

    def _get_total_video(self, path: str) -> int:
        files = os.listdir(path)
        return len(files)
    