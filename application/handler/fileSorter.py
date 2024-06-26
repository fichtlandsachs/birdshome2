import os
import pathlib
import shutil
from time import sleep
import datetime
import cv2
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application import constants
from concurrent.futures.thread import ThreadPoolExecutor

from application import create_app
from application.models import appConfig

app = current_app


class FileSorter:
    def __init__(self):
        self.app = app
        self.videos = []
        self.path_vid_files = os.path.join(app.root_path, self.app.config[constants.OUTPUT_FOLDER],
                                           self.app.config[constants.VIDEO_FOLDER])
        self.createFolderStruct()
        self.dbURL = str(app.config[constants.SQLALCHEMY_DATABASE_URI])
        self.session, self.conn = self.createConnectionDB(self.dbURL)
        self.time_Run_analyser = None
        self.analyser_is_active = False
        app.logger.debug(__name__ + ' initialized')

    def updateConfig(self):
        self.time_Run_analyser = self.getConfigEntry(self.session, constants.VID_ANALYSER,
                                                     constants.VID_ANALYSER_TIME_RUN)
        val = self.getConfigEntry(self.session, constants.VID_ANALYSER,
                                                          constants.VID_ANALYSER_ENABLED)
        if val is not None and val == 'True':
            self.analyser_is_active = True
        else:
            self.analyser_is_active = False

    def analyseFiles(self):
        while True:
            try:
                self.updateConfig()
                if self.analyser_is_active:
                    app.logger.debug('file analyser active')
                    self.createFolderStruct()
                    self.getFiles()
                else:
                    app.logger.debug('file analyser not active. Waiting')
                sleep(60)
            except Exception as e:
                app.logger.error(e.args[0])

    def checkConfigEntryExists(self, session, app_area, config_key):
        entry = session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
        session.close()
        if entry is None:
            return False
        else:
            return True

    def getConfigEntry(self, session, app_area, config_key):
        if self.checkConfigEntryExists(session, app_area, config_key):
            entry = session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
            session.close()
            if entry is not None:
                return entry.config_value
            else:
                return None
        else:
            return None

    def createUpdateConfigEntry(self, session, app_area, config_key, config_value):
        if self.checkConfigEntryExists(session, app_area, config_key):
            entry = session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
            entry.config_value = config_value
        else:
            configRecord = appConfig()
            configRecord.config_area = app_area
            configRecord.config_key = config_key
            configRecord.config_value = config_value
            session.add(configRecord)
        session.commit()
        session.close()

    def createConnectionDB(self, dbUrl):
        try:
            engine = create_engine(dbUrl)
            conn = engine.connect()
            Session = sessionmaker(bind=engine)
            session = Session()
        except Exception as e:
            app.logger.debug(e.args)
        return session, conn

    def createFolderStruct(self):
        if not os.path.exists(os.path.join(self.path_vid_files, 'nodetect')):
            os.makedirs(os.path.join(self.path_vid_files, 'nodetect'))
        if not os.path.exists(os.path.join(self.path_vid_files, 'detect')):
            os.makedirs(os.path.join(self.path_vid_files, 'detect'))
        if not os.path.exists(os.path.join(self.path_vid_files, 'detect', 'less_5000')):
            os.makedirs(os.path.join(self.path_vid_files, 'detect', 'less_5000'))
        if not os.path.exists(os.path.join(self.path_vid_files, 'detect', 'less_10000')):
            os.makedirs(os.path.join(self.path_vid_files, 'detect', 'less_10000'))
        if not os.path.exists(os.path.join(self.path_vid_files, 'detect', 'above_10000')):
            os.makedirs(os.path.join(self.path_vid_files, 'detect', 'above_10000'))
        #app.logger.debug('folder structure created/ validated')

    def getFiles(self):
        ending = app.config[constants.VID_PREFIX]+'_*.avi'

        vidList:list

        vidList.extend(list(sorted(pathlib.Path(self.path_vid_files).glob(ending), key=os.path.getmtime)))
        app.logger.debug(str(len(vidList))+' files found')
        time_start_str = self.getConfigEntry(self.session, constants.VID_ANALYSER,
                                             constants.VID_ANALYSER_TIME_RUN)
        time_end_str = '04:00'
        time_end_date = datetime.datetime.now()+datetime.timedelta(days=1)

        if int(time_start_str[:2]) > int(time_end_str[:2]):
            start_time_t = datetime.datetime.strptime(
                datetime.datetime.now().strftime('%Y-%m-%d') + 'T' + time_start_str + ':00', '%Y-%m-%dT%H:%M:%S')
            time_end_t = datetime.datetime.strptime(time_end_date.strftime('%Y-%m-%d') + 'T' + time_end_str + ':00', '%Y-%m-%dT%H:%M:%S')
        else:
            start_time_t = datetime.datetime.strptime(
                time_end_date.strftime('%Y-%m-%d') + 'T' + time_start_str + ':00', '%Y-%m-%dT%H:%M:%S')
            time_end_t = datetime.datetime.strptime(time_end_date.strftime('%Y-%m-%d') + 'T' + time_end_str + ':00', '%Y-%m-%dT%H:%M:%S')

        now = datetime.datetime.now()
        app.logger.debug('Time is set from: ' + time_start_str + ' : '+ time_end_str)
        if len(vidList) > 0:
            for vid in vidList:
                if start_time_t < now < time_end_t:
                    self.analyseFile(vid)

    def analyseFile(self, vidListEntry):
        fileName = vidListEntry.as_posix()
        name = vidListEntry.name
        app.logger.debug('analyse file: ' + name)
        if datetime.datetime.utcfromtimestamp(pathlib.Path(vidListEntry).stat().st_ctime) > (
                datetime.datetime.now() - datetime.timedelta(seconds=50)):
            pass

        vr = cv2.VideoCapture(fileName)
        check = True
        # Assigning our static_back to None
        static_back = None
        # List when any moving object appear
        contour_res = 0
        count = 0
        count2 = 0
        motion = 0
        while check:
            # Reading frame(image) from video
            check, frame = vr.read()
            if not check:
                break

            # Initializing motion = 0(no motion)
            motion = 0
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
            if count2 < 9:
                count2 = count2 + 1
                continue
            # Difference between static background
            # and current frame(which is GaussianBlur)
            diff_frame = cv2.absdiff(static_back, gray)

            # If change in between static background and
            # current frame is greater than 30 it will show white color(255)
            thresh_frame = cv2.threshold(diff_frame, 50, 255, cv2.THRESH_BINARY)[1]
            thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

            # Finding contour of moving object
            cnts, hierarchy = cv2.findContours(thresh_frame.copy(),
                                                      cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in cnts:
                if cv2.contourArea(contour) > 3000:
                    contour_res = cv2.contourArea(contour)
                    motion = 1
                    check = False
                    break

            count = count + 1
            count2 = 0
        vr.release()
        if motion == 0:
            path = os.path.join(self.path_vid_files, 'nodetect', str(name))
        else:
            if contour_res <= 5000:
                path = os.path.join(self.path_vid_files, 'detect', 'less_5000', str(name))
            elif contour_res <= 10000:
                path = os.path.join(self.path_vid_files, 'detect', 'less_10000', str(name))
            else:
                path = os.path.join(self.path_vid_files, 'detect', 'above_10000', str(name))

        app.logger.debug('move file to: ' + path)
        shutil.move(fileName, path)
        return motion
