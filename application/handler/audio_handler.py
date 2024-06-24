import datetime
import threading
import wave

import pyaudio


class AudioRecorder(threading.Thread):
    """Audio class based on pyAudio and Wave"""

    def __init__(self, filename: str, recording: datetime, rate: int = 44100, fpb: int = 4096, channels: int = 1):
        threading.Thread.__init__(self)
        self.open = True
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_filename = filename
        self.audio = pyaudio.PyAudio()
        self.recordTime = recording
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.frames_per_buffer)
        self.audio_frames = []

    def run(self):
        "Audio starts being recorded"
        self.stream.start_stream()
        while datetime.datetime.now() < self.recordTime:
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
            if not self.open:
                break
        self.stop()

    def stop(self):
        self.open = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        waveFile = wave.open(self.audio_filename, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.audio_frames))
        waveFile.close()
