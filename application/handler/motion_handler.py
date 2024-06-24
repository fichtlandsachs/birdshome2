import datetime
import os
from time import sleep

import cv2
import numpy as np
from flask import current_app

app = current_app
with app.app_context():
    from application import constants
    from application.handler.audio_handler import AudioRecorder
    from application.handler.database_hndl import DBHandler
    from application.handler.video_audio_merger import AudioVideoMerge
    from application.handler.video_handler import VideoRecorder
    import application as appCfg

class Motion_Handler:

    def __init__(self, vc):

        self.app = app
        self.vc = self.app.config.get(constants.VIDEO_CAPTURE_INST)
        self.video_height = self.app.config.get(constants.PICTURE_LATEST_RES_X)
        self.video_width = self.app.config.get(constants.PICTURE_LATEST_RES_Y)
        self.prefix = self.app.config.get(constants.PICTURE_PREFIX)
        self.db = DBHandler(app.config.get(constants.SQLALCHEMY_DATABASE_URI))
        self.folderName = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                       app.config.get(constants.VIDEO_FOLDER))
        self.nextScreenShot = datetime.datetime.now() + datetime.timedelta(
            minutes=int(app.config[constants.REPLAY_INTERVAL]))
        self.app.logger.debug('Motion_Handler initialized')

    def updateConfigFromDB(self):
        self.app = appCfg.get_configuration_data_db(self.app)
        self.app.logger.debug('Motion_Handler: Configuration updated')

    def detect(self):
        try:
            # Assigning our static_back to None
            static_back = None
            count = 0
            # Initializing DataFrame, one column is start
            # time and other column is end time
            nextReadTime = datetime.datetime.now() + datetime.timedelta(minutes=10)
            sensitivity = None
            X = int(self.app.config.get(constants.VID_RES_X))
            Y = int(self.app.config.get(constants.VID_RES_Y))
            self.app.logger.info('Motion_Handler: Motion_Handler start detection')
            while True:
                if not app.config.get(constants.MOTION_HANDLING_ENABLED):
                    sleep(60)
                    continue
                if datetime.datetime.now() > nextReadTime or sensitivity is None:
                    sensitivity = int(self.app.config[constants.MOTION_HANDLING_SENSITIVITY])
                    nextReadTime = datetime.datetime.now() + datetime.timedelta(minutes=10)
                # Reading frame(image) from video

                frame = np.empty((X, Y, 3), dtype=np.uint8)

                check, frame = self.vc.read(frame)
                if check:
                    # Converting color image to gray_scale image
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # Converting gray scale image to GaussianBlur
                    # so that change can be find easily
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)

                    # In first iteration we assign the value
                    # of static_back to our first frame
                    if static_back is None:
                        static_back = gray
                        continue
                    if count == 100:
                        static_back = gray
                        count = 0
                    # Difference between static background
                    # and current frame(which is GaussianBlur)
                    diff_frame = cv2.absdiff(static_back, gray)

                    # If change in between static background and
                    # current frame is greater than 30 it will show white color(255)
                    thresh_frame = cv2.threshold(diff_frame, 50, 255, cv2.THRESH_BINARY)[1]
                    thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

                    # Finding contour of moving object
                    cnts, _ = cv2.findContours(thresh_frame.copy(),
                                                  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for contour in cnts:
                        if cv2.contourArea(contour) < sensitivity:
                            continue
                        self.app.logger.debug('Motion_Handler: motion detected')
                        self.startRecording()
                        sleep(5)
                        self.updateConfigFromDB()
                else:
                    self.app.logger.error('Motion_Handler: no picture from camera')
                sleep(.33)
                count = count + 1
        except Exception as e:
            self.app.logger.error(e.args[0])
            self.db.close()

    def startRecording(self):
        self.app.logger.info('Motion_Handler: start recording')
        timeFormat = self.app.config[constants.TIME_FORMAT_FILE]
        timestamp_file = datetime.datetime.now().strftime(timeFormat)
        fileVideo_short = self.prefix + timestamp_file + self.app.config.get(constants.VID_FORMAT)
        fileAudio_short = self.prefix + timestamp_file + self.app.config.get(constants.VID_SOUND_FORMAT)
        full_FileName = self.prefix + '_' + timestamp_file + self.app.config.get(constants.VID_FORMAT)
        full_VideoFile = os.path.join(self.folderName, fileVideo_short)
        full_AudioFile = os.path.join(self.folderName, fileAudio_short)
        full_finalFile = os.path.join(self.folderName, full_FileName)
        self.app.logger.debug('Motion_Handler: final File Name: ' + full_finalFile)
        self.record(full_finalFile, full_VideoFile, full_AudioFile)

    def record(self, full_filename, video_fileName, audio_fileName):
        self.app.logger.debug('Motion_Handler: create Tasks for Audio and video recording')
        delta = int(self.app.config.get(constants.VID_DURATION))
        endTime = datetime.datetime.now() + datetime.timedelta(seconds=delta)
        vHandler = VideoRecorder(video_fileName, endTime, self.app, self.vc)
        aHandler = AudioRecorder(audio_fileName, endTime)

        threads = []
        vHandler.start()
        aHandler.start()

        threads.append(vHandler)
        threads.append(aHandler)

        for t in threads:
            t.join()
        vHandler.stop()
        aHandler.stop()
        self.app.logger.debug('merge audio and video Files')
        mHandler = AudioVideoMerge(full_filename, video_fileName, audio_fileName, self.app)
        mHandler.start()

    def stop(self):
        self.db.close()
