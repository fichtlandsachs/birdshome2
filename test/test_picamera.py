from subprocess import call

import numpy as np
import picamera
import picamera.array


class DetectMotion(picamera.array.PiMotionAnalysis):
    def analyze(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
        ).clip(0, 255).astype(np.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > 60).sum() > 10:
            print('Motion detected!')


with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        camera.resolution = (1280, 720)
        camera.framerate = 25
        camera.start_recording(
            'motion.h264')
        camera.wait_recording(40)
        camera.stop_recording()
        command = "MP4Box -add motion.h264 motion.mp4"
        # Execute our command
        call([command], shell=True)
        command = "rm motion.h264"
        call([command], shell=True)
