import datetime
import pathlib
from time import sleep

import numpy as np
import requests
import os
import cv2, flask
from flask import current_app

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from application.models import appConfig
import application.constants as constants

app = current_app


class ScreenShotHandler:
    def __init__(self, vc):
        try:
            self.app: flask.app = app
            self.vr: cv2.VideoCapture = self.app.config.get(constants.VIDEO_CAPTURE_INST)
            self.lastRun = None
            self.dbPath: str = self.app.config.get(constants.SQLALCHEMY_DATABASE_URI)
            self.session, self.conn = self.createConnectionDB(self.dbPath)
            self.active: bool = self.app.config.get(constants.REPLAY_ENABLED)
            self.intervall: int = self.app.config.get(constants.REPLAY_INTERVAL)
            self.lastrun = self.getConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_RUN_SCREEN)
            self.daysReplay: int = self.app.config.get(constants.REPLAY_DAYS)
            self.lastRunReplay: datetime = self.getConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_STARTTIME)
            self.fourcc: cv2.CAP_PROP_FOURCC = self.app.config.get(constants.VID_FOURCC)
            self.app.logger.info('ScreenShotHandler: ScreenShotHandler initialized')
        except Exception as e:
            self.app.logger.error(e.args)

    def updateConfig(self):
        self.dbPath = str(self.app.config.get(constants.SQLALCHEMY_DATABASE_URI))
        self.session, self.conn = self.createConnectionDB(dbUrl=self.dbPath)
        self.active = int(self.app.config.get(constants.REPLAY_ENABLED))
        self.intervall = int(self.app.config.get(constants.REPLAY_INTERVAL))
        self.lastrun = self.getConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_RUN_SCREEN)
        self.daysReplay = self.app.config.get(constants.REPLAY_DAYS)
        self.lastRunReplay = self.getConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_STARTTIME)
        self.fourcc = self.app.config.get(constants.VID_FOURCC)
        self.app.logger.debug('ScreenShotHandler: Configuration updated from database')

    def createScreenShot(self):
        fileName_short = app.config.get(constants.PICTURE_PREFIX) + datetime.datetime.now().strftime(
            app.config.get(constants.TIME_FORMAT_FILE)) + '.' + str(
            app.config.get(constants.PICTURE_ENDING))
        full_filename = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                     app.config.get(constants.SCREENSHOT_FOLDER),

                                     fileName_short)
        frame = np.array((int(app.config.get(constants.VID_RES_X)), int(app.config.get(constants.VID_RES_Y)), 3),
                         dtype=np.uint8)
        check, frame = self.vr.read(frame)
        if check:
            image_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
            cv2.imwrite(full_filename, image_gray)
        self.app.logger.debug('ScreenShotHandler: File created: ' + full_filename)

    def createReplay(self):
        screenShots = list()
        pattern = '*.jpg'
        screen_path = self.app.config.get(constants.REPLAY_SCREENSHOT_PATH)
        self.app.logger.debug('ScreenShotHandler: path to screenshots is: ' + screen_path)
        screenShots.extend(list(sorted(pathlib.Path(screen_path).glob(pattern), key=os.path.getmtime,
                                       reverse=False)))
        self.app.logger.debug(str(len(screenShots)) + 'Files found')
        fps = self.app.config.get(constants.REPLAY_FRAMES_PER_SEC)
        file_prefix = self.app.config.get(constants.REPLAY_PREFIX_VID)
        dateFormat = self.app.config.get(constants.TIME_FORMAT_FILE)
        file_ending = self.app.config.get(constants.VID_FORMAT)
        full_fileName = file_prefix + self.lastrun.strftime(dateFormat) + file_ending
        full_VideoFile = os.path.join(str(self.app.config.get(constants.REPLAY_PATH)), full_fileName)
        if len(screenShots) > 0:
            fourcc = cv2.cv2.VideoWriter_fourcc(*'avc1')
            vid_Out = cv2.cv2.VideoWriter(full_VideoFile, fourcc, int(fps),
                                          (1280, 720),
                                          False)
            for screen in screenShots:
                frame = cv2.cv2.imread(filename=str(screen), flags=cv2.IMREAD_GRAYSCALE)
                vid_Out.write(frame)
            vid_Out.release()
            self.app.logger.debug('ScreenShotHandler: Replay created: ' + full_fileName)
            for screen in screenShots:
                os.remove(screen)

    def createConnectionDB(self, dbUrl):
        try:
            engine = create_engine(dbUrl)
            conn = engine.connect()
            Session = sessionmaker(bind=engine)
            session = Session()
            self.app.logger.debug('ScreenShotHandler: Database connection created')
            return session, conn
        except Exception as e:
            self.app.logger.error(e.args)

    def getLastRundScreenShotMaker(self):
        lastRun = self.getConfigEntry(constants.REPLAY, constants.REPLAY_LAST_RUN_SCREEN)
        if lastRun != None:
            self.createUpdateConfigEntry(constants.REPLAY, constants.REPLAY_LAST_RUN_SCREEN,
                                         datetime.datetime.now().strftime(constants.DATETIME_FORMAT))
            return datetime.datetime.now()
        return lastRun

    def checkConfigEntryExists(self, session, app_area, config_key):
        entry = session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
        session.close()
        if entry is None:
            self.app.logger.debug('ScreenShotHandler: '+app_area + '' + config_key + '' + 'not found')
            return False
        else:
            self.app.logger.debug('ScreenShotHandler: '+app_area + '' + config_key + '' + 'found')
            return True

    def getConfigEntry(self, session, app_area, config_key):
        if self.checkConfigEntryExists(session, app_area, config_key):
            entry = session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
            session.close()
            self.app.logger.debug('ScreenShotHandler: '+app_area + '' + config_key + '' + entry.config_value + '' + 'not found')
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
            self.app.logger.debug('ScreenShotHandler: '+app_area + '' + config_key + '' + config_value + '' + 'is set')
        else:
            configRecord = appConfig()
            configRecord.config_area = app_area
            configRecord.config_key = config_key
            configRecord.config_value = config_value
            session.add(configRecord)
            self.app.logger.debug('ScreenShotHandler: '+app_area + '' + config_key + '' + config_value + '' + 'is added')
        session.commit()
        session.close()

    def start_Replay(self):
        while True:
            try:
                self.app.logger.debug('ScreenShotHandler: '+__name__ + 'is started')
                self.updateConfig()
                if self.active == 1:

                    if self.lastRunReplay is None:
                        self.createUpdateConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_STARTTIME,
                                                     datetime.datetime.now().strftime(constants.DATETIME_FORMAT_DATE))
                        self.lastRunReplay = self.app.config[constants.REPLAY_LAST_STARTTIME] = datetime.datetime.now().strftime(
                            constants.DATETIME_FORMAT_DATE)
                    if self.lastrun is None:
                        self.createScreenShot()
                        self.createUpdateConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_RUN_SCREEN,
                                                     datetime.datetime.now().strftime(constants.DATETIME_FORMAT))

                    else:
                        if self.lastrun == None:
                            self.lastrun = datetime.datetime.now()
                        self.lastrun = datetime.datetime.strptime(self.lastrun, constants.DATETIME_FORMAT)
                        intervall = self.intervall * 60
                        nextRun = self.lastrun + datetime.timedelta(seconds=intervall)
                        if nextRun < datetime.datetime.now():
                            self.createScreenShot()
                            self.createUpdateConfigEntry(self.session, constants.REPLAY,
                                                         constants.REPLAY_LAST_RUN_SCREEN,
                                                         datetime.datetime.now().strftime(constants.DATETIME_FORMAT))
                    if not self.checkConfigEntryExists(session=self.session, app_area=constants.REPLAY,
                                                       config_key=constants.REPLAY_LAST_STARTTIME):
                        self.createUpdateConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_STARTTIME,
                                                     datetime.datetime.now().strftime(constants.DATETIME_FORMAT_DATE))

                    nextReplayDate = datetime.datetime.strptime(self.lastRunReplay,
                                                                constants.DATETIME_FORMAT_DATE) + datetime.timedelta(
                        days=int(self.daysReplay))
                    if nextReplayDate < datetime.datetime.now():
                        self.app.logger.debug('ScreenShotHandler: '+__name__ + 'Time is over create replay now')
                        self.createReplay()
                        self.createUpdateConfigEntry(self.session, constants.REPLAY, constants.REPLAY_LAST_STARTTIME,
                                                     datetime.datetime.now().strftime(constants.DATETIME_FORMAT_DATE))
                    self.app.logger.debug(__name__ + 'is active. Waiting now')
                    sleep(self.intervall * 60)
                else:
                    self.app.logger.debug('ScreenShotHandler: '+__name__ + 'is not set to active. Waiting....')
                    sleep(self.intervall * 60)
            except Exception as e:
                self.app.logger.error(e.args[0])
