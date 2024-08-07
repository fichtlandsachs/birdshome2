"""server configuration"""
SECRET_KEY = 'SECRET_KEY'
TIME_FORMAT_FILE = 'TIME_FORMAT_FILE'
TEMPLATES_AUTO_RELOAD = 'TEMPLATES_AUTO_RELOAD'
TEMPLATES_FOLDER = 'TEMPLATES_FOLDER'
SERVER_NAME = 'SERVER_NAME'
APPLICATION_NAME = 'APPLICATION_NAME'
APPLICATION_USER = 'APPLICATION_USER'
APPLICATION_USER_GRP = 'APPLICATION_USER_GRP'
ROOT_PATH_APPLICATION = 'APPLICATION_ROOT'

LOGGING_LEVEL = 'LOGGING_LEVEL'
LOGGING_FORMAT = 'LOGGING_FORMAT'
LOGGING_FILE_NAME = 'LOGGING_FILE_NAME'
LOGGING_FILE_FOLDER = 'LOGGING_FILE_FOLDER'

"""server upload"""
SERVER_UPLOAD_ENABLED = 'SERVER_UPLOAD_ENABLED'
SERVER_PAUSE_RETRY_UPLOAD = 'SERVER_PAUSE_RETRY_UPLOAD'
SERVER_NUM_RETRY_UPLOAD = 'SERVER_NUM_RETRY_UPLOAD'
SERVER_FOLDER_UPLOAD = 'SERVER_FOLDER_UPLOAD'
SERVER_UPLOAD = 'SERVER_UPLOAD'
SERVER_USER_UPLOAD = 'SERVER_USER_UPLOAD'
SERVER_PASS_UPLOAD = 'SERVER_PASS_UPLOAD'
SERVER_PORT = 'SERVER_PORT'
SERVER_FTP_ENABLED = 'SERVER_PASS_UPLOAD'
SERVER_SMB_ENABLED = 'SERVER_SMB_ENABLED'
SERVER_TIME_UPLOAD = 'SERVER_TIME_UPLOAD'
SERVER_DELETE_AFTER_UPLOAD_ENABLED = 'SERVER_DELETE_AFTER_UPLOAD_ENABLED'

"""Video Configuration"""
VID_DURATION = 'VID_DURATION'
VID_PREFIX = 'VID_PREFIX'
VID_RES_X = 'VID_RES_X'
VID_RES_Y = 'VID_RES_Y'
VID_FRAMES = 'VID_FRAMES'
VID_FOURCC = 'VID_FOURCC'
VID_FORMAT = 'VID_FORMAT'
VID_SOUND_FORMAT = 'VID_SOUND_FORMAT'
VID_ENDINGS = 'VID_ENDINGS'
VID_LABEL_FORMAT = 'VID_LABEL_FORMAT'
VID_ROTATE_ENABLED = 'VID_ROTATE_ENABLED'

"""Replay configuration"""
REPLAY_FRAMES_PER_SEC = 'REPLAY_FRAMES_PER_SEC'
REPLAY_PATH = 'REPLAY_PATH'
REPLAY_ENABLED = 'REPLAY_ENABLED'
REPLAY_SCREENSHOT_PATH = 'REPLAY_SCREENSHOT_PATH'
REPLAY_INTERVAL = 'REPLAY_INTERVAL'
REPLAY_PREFIX_VID = 'REPLAY_PREFIX_VID'
REPLAY_DAYS = 'REPLAY_DAYS'
REPLAY_LAST_RUN_SCREEN = 'REPLAY_LAST_RUN_SCREEN'
REPLAY_LAST_STARTTIME = 'REPLAY_LAST_STARTTIME'

"""Picture configuration"""
PICTURE_PREFIX = 'PICTURE_PREFIX'
PICTURE_ENDING = 'PICTURE_ENDING'
PICTURE_LATEST_RES_X = 'PICTURE_LATEST_RES_X'
PICTURE_LATEST_RES_Y = 'PICTURE_LATEST_RES_Y'

"""Video analytics configuration"""
VID_ANALYSER_TIME_RUN = 'VID_ANALYSER_TIME_RUN'
VID_ANALYSER_ENABLED = 'VID_ANALYSER_ENABLED'
VID_ANALYSER = 'VID_ANALYSER'

"""LandingPage Configuration"""
NAME_BIRD = 'NAME_BIRD'
DATE_CHICK = 'DATE_CHICK'
DATE_EGG = 'DATE_EGG'
FIRST_VISIT = 'FIRST_VISIT'
DATE_LEAVE = 'DATE_LEAVE'

"""motion handling configuration"""
MOTION_HANDLING_ENABLED = 'MOTION_HANDLING_ENABLED'
MOTION_HANDLING_SENSITIVITY = 'MOTION_HANDLING_SENSITIVITY'

""" base configuration"""
SQLALCHEMY_TRACK_MODIFICATIONS = 'SQLALCHEMY_TRACK_MODIFICATIONS'
SQLALCHEMY_DATABASE_URI = 'SQLALCHEMY_DATABASE_URI'
SQLALCHEMY_DATABASE_USER = 'SQLALCHEMY_DATABASE_USER'
SQLALCHEMY_DATABASE_PASSW = 'SQLALCHEMY_DATABASE_PASSW'

OUTPUT_FOLDER = 'OUTPUT_FOLDER'
MEDIA_FOLDER = 'MEDIA_FOLDER'
DEBUG = 'DEBUG'
VIDEO_FOLDER = 'VIDEO_FOLDER'
SCREENSHOT_FOLDER = 'SCREENSHOT_FOLDER'
NO_DETECT_FOLDER = 'NO_DETECT_FOLDER'
PERSONAS_FOLDER = 'PERSONAS_FOLDER'
DATABASE_FOLDER = 'DATABASE_FOLDER'
REPLAY_FOLDER = 'REPLAY_FOLDER'
PICTURE_FOLDER = 'PICTURE_FOLDER'

# Video Settings
VIDEO_CAPTURE_INST = 'VIDEO_CAPTURE_INST'

# group contig Entries
NEST_CONFIG = 'NEST_CONFIG'
REPLAY = 'REPLAY'
VIDEO = 'VIDEO'
MOTION = 'MOTION'
SYSTEM = 'SYSTEM'
PICTURE = 'PICTURE'
SMB = 'SMB'
DATA = 'DATA'
# general settings
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
SERVER_DATETIME_FORMAT = "%H:%M"
DATETIME_FORMAT_DATE = "%d.%m.%Y"
DATETIME_FORMATE_UI = '%Y-%m-%dT%H:%M:%S'
DATEFORMATE_FILE_SEL = '%Y-%m-%d'
