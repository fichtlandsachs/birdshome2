import json
import os
import socket
from grp import getgrnam
from pwd import getpwnam

from logging.handlers import RotatingFileHandler

import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DevConfig, ProdConfig

from application import constants

db = SQLAlchemy()


def update_Config(app_config, db_value):
    if db_value is not None:
        app_config = db_value
    return app_config


def get_configuration_data_db(app):
    from application.handler.database_hndl import DBHandler
    _db = DBHandler(app.config.get(constants.SQLALCHEMY_DATABASE_URI))

    update_Config(app.config[constants.SECRET_KEY], _db.getConfigEntry(constants.SYSTEM, constants.SECRET_KEY))
    update_Config(app.config[constants.TIME_FORMAT_FILE], _db.getConfigEntry(constants.SYSTEM, constants.TIME_FORMAT_FILE))

    """server configuration"""

    update_Config(app.config[constants.SERVER_NAME] , _db.getConfigEntry(constants.SYSTEM, constants.SERVER_NAME))
    update_Config(app.config[constants.APPLICATION_NAME] , _db.getConfigEntry(constants.SYSTEM, constants.APPLICATION_NAME))
    update_Config(app.config[constants.APPLICATION_USER] , _db.getConfigEntry(constants.SYSTEM, constants.APPLICATION_USER))
    update_Config(app.config[constants.APPLICATION_USER_GRP] , _db.getConfigEntry(constants.SYSTEM, constants.APPLICATION_USER_GRP))
    update_Config(app.config[constants.LOGGING_LEVEL] , _db.getConfigEntry(constants.SYSTEM, constants.LOGGING_LEVEL))
    update_Config(app.config[constants.LOGGING_FILE_NAME] , _db.getConfigEntry(constants.SYSTEM, constants.LOGGING_FILE_NAME))
    update_Config(app.config[constants.LOGGING_FORMAT] , _db.getConfigEntry(constants.SYSTEM, constants.LOGGING_FORMAT))
    update_Config(app.config[constants.LOGGING_FILE_FOLDER], _db.getConfigEntry(constants.SYSTEM, constants.LOGGING_FILE_FOLDER))
    """Server upload"""
    update_Config(app.config[constants.SERVER_UPLOAD_ENABLED] , _db.getConfigEntry(constants.SMB, constants.SERVER_UPLOAD_ENABLED))
    update_Config(app.config[constants.SERVER_PAUSE_RETRY_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_PAUSE_RETRY_UPLOAD))
    update_Config(app.config[constants.SERVER_NUM_RETRY_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_NUM_RETRY_UPLOAD))
    update_Config(app.config[constants.SERVER_FOLDER_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_FOLDER_UPLOAD))
    update_Config(app.config[constants.SERVER_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_UPLOAD))
    update_Config(app.config[constants.SERVER_USER_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_USER_UPLOAD))
    update_Config(app.config[constants.SERVER_PASS_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_PASS_UPLOAD))
    update_Config(app.config[constants.SERVER_FTP_ENABLED] , _db.getConfigEntry(constants.SMB, constants.SERVER_FTP_ENABLED))
    update_Config(app.config[constants.SERVER_SMB_ENABLED]  , _db.getConfigEntry(constants.SMB, constants.SERVER_SMB_ENABLED))
    update_Config(app.config[constants.SERVER_TIME_UPLOAD] , _db.getConfigEntry(constants.SMB, constants.SERVER_TIME_UPLOAD))
    update_Config(app.config[constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED] , _db.getConfigEntry(constants.SMB, constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED))

    """Video Configuration"""
    update_Config(app.config[constants.VID_DURATION] , _db.getConfigEntry(constants.VIDEO, constants.VID_DURATION))
    update_Config(app.config[constants.VID_PREFIX] , _db.getConfigEntry(constants.VIDEO, constants.VID_PREFIX))
    update_Config(app.config[constants.VID_RES_X] , _db.getConfigEntry(constants.VIDEO, constants.VID_RES_X))
    update_Config(app.config[constants.VID_RES_Y] , _db.getConfigEntry(constants.VIDEO, constants.VID_RES_Y))
    update_Config(app.config[constants.VID_FRAMES] , _db.getConfigEntry(constants.VIDEO, constants.VID_FRAMES))
    update_Config(app.config[constants.VID_FOURCC] , _db.getConfigEntry(constants.VIDEO, constants.VID_FOURCC))
    update_Config(app.config[constants.VID_FORMAT] , _db.getConfigEntry(constants.VIDEO, constants.VID_FORMAT))
    update_Config(app.config[constants.VID_SOUND_FORMAT] , _db.getConfigEntry(constants.VIDEO, constants.VID_SOUND_FORMAT))
    update_Config(app.config[constants.VID_ENDINGS] , _db.getConfigEntry(constants.VIDEO, constants.VID_ENDINGS))
    update_Config(app.config[constants.VID_ROTATE_ENABLED] , _db.getConfigEntry(constants.VIDEO, constants.VID_ROTATE_ENABLED))

    """Replay configuration"""
    update_Config(app.config[constants.REPLAY_FRAMES_PER_SEC] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_FRAMES_PER_SEC))
    update_Config(app.config[constants.REPLAY_PATH] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_PATH))
    update_Config(app.config[constants.REPLAY_ENABLED] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_ENABLED))
    update_Config(app.config[constants.REPLAY_SCREENSHOT_PATH] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_SCREENSHOT_PATH))
    update_Config(app.config[constants.REPLAY_INTERVAL] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_INTERVAL))
    update_Config(app.config[constants.REPLAY_PREFIX_VID] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_PREFIX_VID))
    update_Config(app.config[constants.REPLAY_DAYS] , _db.getConfigEntry(constants.REPLAY, constants.REPLAY_DAYS))

    """Picture configuration"""
    update_Config(app.config[constants.PICTURE_PREFIX] , _db.getConfigEntry(constants.PICTURE, constants.PICTURE_PREFIX))
    update_Config(app.config[constants.PICTURE_ENDING] , _db.getConfigEntry(constants.PICTURE, constants.PICTURE_ENDING))
    update_Config(app.config[constants.PICTURE_LATEST_RES_X] , _db.getConfigEntry(constants.PICTURE, constants.PICTURE_LATEST_RES_X))
    update_Config(app.config[constants.PICTURE_LATEST_RES_Y] , _db.getConfigEntry(constants.PICTURE, constants.PICTURE_LATEST_RES_Y))

    """Video analytics configuration"""
    update_Config(app.config[constants.VID_ANALYSER_TIME_RUN] , _db.getConfigEntry(constants.VID_ANALYSER, constants.VID_ANALYSER_TIME_RUN))
    update_Config(app.config[constants.VID_ANALYSER_ENABLED] , _db.getConfigEntry(constants.VID_ANALYSER, constants.VID_ANALYSER_ENABLED))

    """LandingPage Configuration"""
    update_Config(app.config[constants.NAME_BIRD] , _db.getConfigEntry(constants.SYSTEM, constants.NAME_BIRD))
    update_Config(app.config[constants.DATE_CHICK] , _db.getConfigEntry(constants.SYSTEM, constants.DATE_CHICK))
    update_Config(app.config[constants.DATE_EGG] , _db.getConfigEntry(constants.SYSTEM, constants.DATE_EGG))
    update_Config(app.config[constants.FIRST_VISIT] , _db.getConfigEntry(constants.SYSTEM, constants.FIRST_VISIT))
    update_Config(app.config[constants.DATE_LEAVE] , _db.getConfigEntry(constants.SYSTEM, constants.DATE_LEAVE))

    """motion handling configuration"""
    update_Config(app.config[constants.MOTION_HANDLING_SENSITIVITY] , _db.getConfigEntry(constants.MOTION, constants.MOTION_HANDLING_SENSITIVITY))
    update_Config(app.config[constants.MOTION_HANDLING_ENABLED] , _db.getConfigEntry(constants.MOTION, constants.MOTION_HANDLING_ENABLED))

    """database configuration"""
    update_Config(app.config[constants.SQLALCHEMY_TRACK_MODIFICATIONS] , _db.getConfigEntry(constants.DATA, constants.SQLALCHEMY_TRACK_MODIFICATIONS))
    update_Config(app.config[constants.SQLALCHEMY_DATABASE_URI] , _db.getConfigEntry(constants.DATA, constants.SQLALCHEMY_DATABASE_URI))
    update_Config(app.config[constants.SQLALCHEMY_DATABASE_USER] , _db.getConfigEntry(constants.DATA, constants.SQLALCHEMY_DATABASE_USER))
    update_Config(app.config[constants.SQLALCHEMY_DATABASE_PASSW] , _db.getConfigEntry(constants.DATA, constants.SQLALCHEMY_DATABASE_PASSW))

def get_configuration_data(app: flask.app):
    mode = os.getenv('APPLICATION_MODE')
    if mode == 'DEV':
        app.config.from_object(DevConfig())
    else:
        app.config.from_object(ProdConfig())
    get_configuration_data_db(app)


def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    get_configuration_data(app)

    path_media = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                              app.config.get(constants.MEDIA_FOLDER))
    path_database = os.path.join(app.root_path, app.config.get(constants.DATABASE_FOLDER))

    path_video = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                              app.config.get(constants.VIDEO_FOLDER))
    path_photo = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                              app.config.get(constants.PICTURE_FOLDER))
    path_replay = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                               app.config.get(constants.REPLAY_FOLDER))
    path_screenshots = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                    app.config.get(constants.SCREENSHOT_FOLDER))
    path_general = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                app.config.get(constants.PERSONAS_FOLDER))
    path_logging = os.path.join(app.root_path, app.config.get(constants.LOGGING_FILE_FOLDER))

    check_create_folder(app, path_logging)
    check_create_folder(app, path_media)
    check_create_folder(app, path_database)
    check_create_folder(app, path_screenshots)
    check_create_folder(app, path_replay)
    check_create_folder(app, path_general)
    check_create_folder(app, path_photo)
    check_create_folder(app, path_video)

    birdloggerhandler = RotatingFileHandler(os.path.join(path_logging, app.config.get(constants.LOGGING_FILE_NAME)), maxBytes=5*1024*1024, backupCount=3)
    app.logger.addHandler(birdloggerhandler)

    db.init_app(app)
    app.app_context().push()
    with app.app_context():
        from . import models
        from . import routes
        engine = db.engine
        db.metadata.create_all(bind=engine, checkfirst=True)
        app = write_Configuration_db(app)
        return app


def check_create_folder(app, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        os.chown(folder_name, getpwnam(app.config.get(constants.APPLICATION_USER))[2],
                 getgrnam(app.config.get(constants.APPLICATION_USER_GRP))[2])


def write_Configuration_db(_app):
    entries: list = []
    from application.handler.database_hndl import DBHandler
    _db = DBHandler(_app.config.get(constants.SQLALCHEMY_DATABASE_URI))

    entries.append([constants.SYSTEM, constants.SECRET_KEY, _app.config.get(constants.SECRET_KEY)])
    entries.append([constants.SYSTEM, constants.TIME_FORMAT_FILE, _app.config.get(constants.TIME_FORMAT_FILE)])

    """server configuration"""
    entries.append([constants.SYSTEM, constants.SERVER_NAME, _app.config.get(constants.SERVER_NAME)])
    entries.append([constants.SYSTEM, constants.APPLICATION_NAME, _app.config.get(constants.APPLICATION_NAME)])
    entries.append([constants.SYSTEM, constants.APPLICATION_USER, _app.config.get(constants.APPLICATION_USER)])
    entries.append([constants.SYSTEM, constants.APPLICATION_USER_GRP, _app.config.get(constants.APPLICATION_USER_GRP)])
    entries.append([constants.SYSTEM, constants.LOGGING_LEVEL, _app.config.get(constants.LOGGING_LEVEL)])
    entries.append([constants.SYSTEM, constants.LOGGING_FILE_NAME, _app.config.get(constants.LOGGING_FILE_NAME)])
    entries.append([constants.SYSTEM, constants.LOGGING_FORMAT, _app.config.get(constants.LOGGING_FORMAT)])
    entries.append([constants.SYSTEM, constants.LOGGING_FILE_FOLDER, _app.config.get(constants.LOGGING_FILE_FOLDER)])
    """Server upload"""
    entries.append([constants.SMB, constants.SERVER_UPLOAD_ENABLED, _app.config.get(constants.SERVER_UPLOAD_ENABLED)])
    entries.append([constants.SMB, constants.SERVER_PAUSE_RETRY_UPLOAD, _app.config.get(constants.SERVER_PAUSE_RETRY_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_NUM_RETRY_UPLOAD, _app.config.get(constants.SERVER_NUM_RETRY_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_FOLDER_UPLOAD, _app.config.get(constants.SERVER_FOLDER_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_UPLOAD, _app.config.get(constants.SERVER_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_USER_UPLOAD, _app.config.get(constants.SERVER_USER_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_PASS_UPLOAD, _app.config.get(constants.SERVER_PASS_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_FTP_ENABLED, _app.config.get(constants.SERVER_FTP_ENABLED)])
    entries.append([constants.SMB, constants.SERVER_SMB_ENABLED, _app.config.get(constants.SERVER_SMB_ENABLED)])
    entries.append([constants.SMB, constants.SERVER_TIME_UPLOAD, _app.config.get(constants.SERVER_TIME_UPLOAD)])
    entries.append([constants.SMB, constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED, _app.config.get(constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED)])
    """Video Configuration"""
    entries.append([constants.VIDEO, constants.VID_DURATION, _app.config.get(constants.VID_DURATION)])
    entries.append([constants.VIDEO, constants.VID_PREFIX, _app.config.get(constants.VID_PREFIX)])
    entries.append([constants.VIDEO, constants.VID_RES_X, _app.config.get(constants.VID_RES_X)])
    entries.append([constants.VIDEO, constants.VID_RES_Y, _app.config.get(constants.VID_RES_Y)])
    entries.append([constants.VIDEO, constants.VID_FRAMES, _app.config.get(constants.VID_FRAMES)])
    entries.append([constants.VIDEO, constants.VID_FOURCC, _app.config.get(constants.VID_FOURCC)])
    entries.append([constants.VIDEO, constants.VID_FORMAT, _app.config.get(constants.VID_FORMAT)])
    entries.append([constants.VIDEO, constants.VID_SOUND_FORMAT, _app.config.get(constants.VID_SOUND_FORMAT)])
    entries.append([constants.VIDEO, constants.VID_ENDINGS, _app.config.get(constants.VID_ENDINGS)])
    entries.append([constants.VIDEO, constants.VID_ROTATE_ENABLED, _app.config.get(constants.VID_ROTATE_ENABLED)])

    """Replay configuration"""
    entries.append([constants.REPLAY, constants.REPLAY_FRAMES_PER_SEC, _app.config.get(constants.REPLAY_FRAMES_PER_SEC)])
    entries.append([constants.REPLAY, constants.REPLAY_PATH, _app.config.get(constants.REPLAY_PATH)])
    entries.append([constants.REPLAY, constants.REPLAY_ENABLED, _app.config.get(constants.REPLAY_ENABLED)])
    entries.append([constants.REPLAY, constants.REPLAY_SCREENSHOT_PATH, _app.config.get(constants.REPLAY_SCREENSHOT_PATH)])
    entries.append([constants.REPLAY, constants.REPLAY_INTERVAL, _app.config.get(constants.REPLAY_INTERVAL)])
    entries.append([constants.REPLAY, constants.REPLAY_PREFIX_VID, _app.config.get(constants.REPLAY_PREFIX_VID)])
    entries.append([constants.REPLAY, constants.REPLAY_DAYS, _app.config.get(constants.REPLAY_DAYS)])

    """Picture configuration"""
    entries.append([constants.PICTURE, constants.PICTURE_PREFIX, _app.config.get(constants.PICTURE_PREFIX)])
    entries.append([constants.PICTURE, constants.PICTURE_ENDING, _app.config.get(constants.PICTURE_ENDING)])
    entries.append([constants.PICTURE, constants.PICTURE_LATEST_RES_X, _app.config.get(constants.PICTURE_LATEST_RES_X)])
    entries.append([constants.PICTURE, constants.PICTURE_LATEST_RES_Y, _app.config.get(constants.PICTURE_LATEST_RES_Y)])

    """Video analytics configuration"""
    entries.append([constants.VID_ANALYSER, constants.VID_ANALYSER_TIME_RUN, _app.config.get(constants.VID_ANALYSER_TIME_RUN)])
    entries.append([constants.VID_ANALYSER, constants.VID_ANALYSER_ENABLED, _app.config.get(constants.VID_ANALYSER_ENABLED)])

    """LandingPage Configuration"""
    entries.append([constants.SYSTEM, constants.NAME_BIRD, _app.config.get(constants.NAME_BIRD)])
    entries.append([constants.SYSTEM, constants.DATE_CHICK, _app.config.get(constants.DATE_CHICK)])
    entries.append([constants.SYSTEM, constants.DATE_EGG, _app.config.get(constants.DATE_EGG)])
    entries.append([constants.SYSTEM, constants.FIRST_VISIT, _app.config.get(constants.FIRST_VISIT)])
    entries.append([constants.SYSTEM, constants.DATE_LEAVE, _app.config.get(constants.DATE_LEAVE)])

    """motion handling configuration"""
    entries.append([constants.MOTION, constants.MOTION_HANDLING_SENSITIVITY, _app.config.get(constants.MOTION_HANDLING_SENSITIVITY)])
    entries.append([constants.MOTION, constants.MOTION_HANDLING_ENABLED, _app.config.get(constants.MOTION_HANDLING_ENABLED)])

    """database configuration"""
    entries.append([constants.DATA, constants.SQLALCHEMY_TRACK_MODIFICATIONS, _app.config.get(constants.SQLALCHEMY_TRACK_MODIFICATIONS)])
    entries.append([constants.DATA, constants.SQLALCHEMY_DATABASE_URI, _app.config.get(constants.SQLALCHEMY_DATABASE_URI)])
    entries.append([constants.DATA, constants.SQLALCHEMY_DATABASE_USER, _app.config.get(constants.SQLALCHEMY_DATABASE_USER)])
    entries.append([constants.DATA, constants.SQLALCHEMY_DATABASE_PASSW, _app.config.get(constants.SQLALCHEMY_DATABASE_PASSW)])

    _db.createUpdateConfigEntryBulk(entries)
    _db.close()
    return _app
