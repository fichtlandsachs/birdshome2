import os
import subprocess
import threading
from time import sleep


class AudioVideoMerge:

    def __init__(self, fileName, videoFile, audioFile, app):
        self.fileName = fileName
        self.videoFile = videoFile
        self.audioFile = audioFile
        self.app = app

    def start(self):
        video_thread = threading.Thread(target=self.merge())
        video_thread.start()

    def merge(self):
        cmd = "ffmpeg -y -i " + self.videoFile + " -i " + self.audioFile + " -vcodec copy -acodec copy " + self.fileName
        subprocess.call(cmd, shell=True)
        if os.path.exists(self.videoFile):
            try:
                os.remove(self.videoFile)
            except FileNotFoundError:
                self.app.logger.info('Video Audio Merger: can not delete ' + self.videoFile)
        if os.path.exists(self.audioFile):
            try:
                os.remove(self.audioFile)
            except FileNotFoundError:
                self.app.logger.info('Viedeo Audio Merger: can not delete' + self.audioFile)
    def stop(self):
        pass
