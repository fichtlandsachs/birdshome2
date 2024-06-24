import os
import wave

import pyaudio


class AudioRecorder:
    """Audio class based on pyAudio and Wave"""

    def __init__(self, filename: str = '', rate: int = 44100, fpb: int = 4096, channels: int = 2):
        self.open = True
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_filename = filename
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.frames_per_buffer)
        self.audio_frames = []

    def record(self):
        """Audio starts being recorded"""
        i = 0
        self.stream.start_stream()
        while i < 100:
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
            if not self.open:
                break
            i = i + 1

    def start(self):
        """Launches the video recording function using a thread"""
        self.record()
        # audio_thread = threading.Thread(target=self.record)
        # audio_thread.start()

    def stop(self):
        """Finishes the audio recording therefore the thread too"""
        if self.open:
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


if __name__ == '__main__':
    filePrefix = 'quickTest.wav'
    videoFolder = os.path.join(os.path.dirname(__file__), '../application', 'static', 'media', 'videos', filePrefix)
    audio = AudioRecorder(videoFolder)
    audio.start()
    audio.stop()
