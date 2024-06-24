import json
import os
import socket
from datetime import datetime


def create_folder_name(path: list):
    complete_path: path
    for path in path:
        complete_path = os.path.join(path)
    return complete_path


class Config:
    DEBUG: bool = False
    TESTING: bool = False

    """server configuration"""
    SECRET_KEY: str
    TIME_FORMAT_FILE: str = '%d%m%Y%H%M%S'
    TEMPLATES_AUTO_RELOAD: bool = True
    TEMPLATES_FOLDER: str = 'templates'
    APPLICATION_NAME: str = socket.gethostname()
    FLASK_DEBUG: int = 0
    FLASK_ENV: str = 'development'

    APPLICATION_USER: str
    APPLICATION_USER_GRP: str
    LOGGING_LEVEL: str = "ERROR"
    LOGGING_FORMAT = "%(asctime)s : %(levelname)s : %(name)s : %(message)s"
    LOGGING_FILE_NAME = "app.log"
    """server upload"""
    SERVER_UPLOAD_ENABLED: bool = False
    SERVER_PAUSE_RETRY_UPLOAD: int = 5
    SERVER_NUM_RETRY_UPLOAD: int = 3
    SERVER_FOLDER_UPLOAD: str
    SERVER_UPLOAD: str
    SERVER_USER_UPLOAD: str
    SERVER_PASS_UPLOAD: str
    SERVER_FTP_ENABLED: bool = False
    SERVER_SMB_ENABLED: bool = False
    SERVER_FOLDER_ENABLED: bool = False
    SERVER_TIME_UPLOAD = '21:00'
    SERVER_DELETE_AFTER_UPLOAD_ENABLED: bool = False

    """Video Configuration"""
    VID_DURATION: int = 15
    VID_PREFIX: str = socket.gethostname() + '_'
    VID_RES_X: int = 1280
    VID_RES_Y: int = 720
    VID_FRAMES: int = 30
    VID_FOURCC: str = 'avc1'
    VID_FORMAT: str = '.avi'
    VID_SOUND_FORMAT: str = '.wav'
    VID_ENDINGS = ['*.mp4', '*.avi']
    VID_LABEL_FORMAT: str = '%d.%m.%Y %H:%M:%S'
    VID_ROTATE_ENABLED: bool = False

    """Replay configuration"""
    REPLAY_ENABLED: bool = False
    REPLAY_FRAMES_PER_SEC = 30
    REPLAY_INTERVAL = 10
    REPLAY_DAYS = 7
    REPLAY_PREFIX_VID: str = socket.gethostname() + '_'
    REPLAY_PATH: str = '/etc/birdshome/application/static/media/replay/'
    REPLAY_SCREENSHOT_PATH: str = '//etc/birdshome/application/static/media/screenshots/'

    """Picture configuration"""
    PICTURE_PREFIX: str = socket.gethostname() + '_'
    PICTURE_ENDING: str = 'jpg'
    PICTURE_LATEST_RES_X = '1280'
    PICTURE_LATEST_RES_Y = '720'

    """Video analytics configuration"""
    VID_ANALYSER_TIME_RUN = '02:00'
    VID_ANALYSER_ENABLED: bool = False

    """LandingPage Configuration"""
    NAME_BIRD = ''
    DATE_CHICK: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_EGG: datetime  = datetime.strptime('01.01.1900', '%d.%m.%Y')
    FIRST_VISIT: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_LEAVE: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')

    """motion handling configuration"""
    MOTION_HANDLING_SENSITIVITY: int = 3000
    MOTION_HANDLING_ENABLED: bool = False

    """database configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:////etc/birdshome/application/database/birdshome_base.db'
    SQLALCHEMY_DATABASE_USER: str
    SQLALCHEMY_DATABASE_PASSW: str

    """folder structure"""
    OUTPUT_FOLDER = os.path.join('static')
    MEDIA_FOLDER = 'media'
    DATABASE_FOLDER = 'database'
    FOLDER_CSV_FILE_OUTPUT = 'outputs'
    REPLAY_FOLDER = os.path.join('media', 'replay')
    PICTURE_FOLDER = os.path.join('media', 'photos')
    FOLDER_CHART = os.path.join('media', 'charts')
    VIDEO_FOLDER = os.path.join('media', 'videos')
    SCREENSHOT_FOLDER = os.path.join('media', 'screenshots')
    NO_DETECT_FOLDER = os.path.join('media', 'videos', 'nodetect')
    PERSONAS_FOLDER = os.path.join('media', 'general')
    LOGGING_FILE_FOLDER = os.path.join('log')


class ProdConfig(Config):
    data: json
    with open("birdshome.json", "r") as jsonfile:
        data = json.load(jsonfile)  # Reading the file
        jsonfile.close()

    DEBUG: bool = False
    TESTING: bool = False

    """server configuration"""
    SECRET_KEY: str = data['system']['secret_key']
    TIME_FORMAT_FILE = data['system']['time_format_file']
    TEMPLATES_AUTO_RELOAD: bool = True
    TEMPLATES_FOLDER = 'templates'
    APPLICATION_NAME = socket.gethostname()
    APPLICATION_USER = data['system']['application_user']
    APPLICATION_USER_GRP = data['system']['application_user_group']

    LOGGING_LEVEL = data['logging']['log_level']
    LOGGING_FORMAT = data['logging']['log_format']
    LOGGING_FILE_NAME = data['logging']['log_file_name']

    """server upload"""
    SERVER_UPLOAD_ENABLED: bool = data['server_upload']['enabled']
    SERVER_PAUSE_RETRY_UPLOAD: int = data['server_upload']['pause_retry']
    SERVER_NUM_RETRY_UPLOAD: int = data['server_upload']['num_retry']
    SERVER_FOLDER_UPLOAD: str = data['server_upload']['folder']
    SERVER_UPLOAD: str = data['server_upload']['server_name']
    SERVER_USER_UPLOAD: str = data['server_upload']['user']
    SERVER_PASS_UPLOAD: str = data['server_upload']['password']
    SERVER_FTP_ENABLED: bool = data['server_upload']['ftp_enabled']
    SERVER_SMB_ENABLED: bool = data['server_upload']['smb_enabled']
    SERVER_TIME_UPLOAD = data['server_upload']['upload_time']
    SERVER_DELETE_AFTER_UPLOAD_ENABLED: bool = data['server_upload']['delete_after_upload']

    """Video Configuration"""
    VID_DURATION: int = data['video']['duration']
    if data['video']['video_prefix'] != '': VID_PREFIX: str = data['video']['video_prefix']
    VID_RES_X: int = data['video']['x_resolution']
    VID_RES_Y: int = data['video']['y_resolution']
    VID_FRAMES: int = data['video']['frames_per_sec']
    VID_FOURCC: str = data['video']['fourcc']
    VID_FORMAT: str = data['video']['video_format']
    VID_SOUND_FORMAT: str = data['video']['output_sound_format']
    VID_ENDINGS = data['video']['output_video_format']
    VID_LABEL_FORMAT: str = data['video']['video_label_format']
    VID_ROTATE_ENABLED: bool = data['video']['video_rotation_enabled']

    """Replay configuration"""
    REPLAY_FRAMES_PER_SEC = data['replay']['frames_per_sec']
    REPLAY_PATH: str = data['replay']['output_path']
    REPLAY_ENABLED: bool = data['replay']['enabled']
    REPLAY_SCREENSHOT_PATH: str = data['replay']['path_snapshots']
    REPLAY_INTERVAL: int = data['replay']['interval']
    REPLAY_PREFIX_VID: str = data['replay']['prefix']
    REPLAY_DAYS: int = data['replay']['replay_interval']

    """Picture configuration"""
    PICTURE_PREFIX: str = socket.gethostname() + '_'
    PICTURE_ENDING: str = 'jpg'
    PICTURE_LATEST_RES_X = '1280'
    PICTURE_LATEST_RES_Y = '720'

    """Video analytics configuration"""
    VID_ANALYSER_TIME_RUN = '02:00'
    VID_ANALYSER_ENABLED: bool = False

    """LandingPage Configuration"""
    NAME_BIRD = ''
    DATE_CHICK: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_EGG: datetime  = datetime.strptime('01.01.1900', '%d.%m.%Y')
    FIRST_VISIT: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_LEAVE: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')

    """motion handling configuration"""
    MOTION_HANDLING_ENABLED: bool = data['motion_detection']['enabled']
    MOTION_HANDLING_SENSITIVITY: int = data['motion_detection']['sensitivity']

    """database configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = data['database']['uri']
    SQLALCHEMY_DATABASE_USER = data['database']['user']
    SQLALCHEMY_DATABASE_PASSW = data['database']['password']

    """folder structure"""
    for folder in data['folder_structure']:
        if folder == "output_folder":
            OUTPUT_FOLDER = create_folder_name(data['folder_structure']['output_folder'])
        elif folder == "media_folder":
            DATABASE_FOLDER = create_folder_name(data['folder_structure']['media_folder'])
        elif folder == "database_folder":
            DATABASE_FOLDER = create_folder_name(data['folder_structure']['database_folder'])
        elif folder == "replay_folder":
            REPLAY_FOLDER = create_folder_name(data['folder_structure']['replay_folder'])
        elif folder == "picture_folder":
            PICTURE_FOLDER = create_folder_name(data['folder_structure']['picture_folder'])
        elif folder == "video_folder":
            VIDEO_FOLDER = create_folder_name(data['folder_structure']['video_folder'])
        elif folder == "screenshot_folder":
            SCREENSHOT_FOLDER = create_folder_name(data['folder_structure']['screenshot_folder'])
        elif folder == "vid_analyser_folder":
            NO_DETECT_FOLDER = create_folder_name(data['folder_structure']['vid_analyser_folder'])
        elif folder == "picture_personas":
            PERSONAS_FOLDER = create_folder_name(data['folder_structure']['picture_personas'])
        elif folder == "logfile_location":
            LOGGING_FILE_FOLDER = create_folder_name(data['folder_structure']['log_file_folder'])

    FLASK_DEBUG = 0
    FLASK_ENV = 'production'


class DevConfig(Config):
    data: json
    with open("birdshome.json", "r") as jsonfile:
        data = json.load(jsonfile)  # Reading the file
        jsonfile.close()

    DEBUG: bool = data['system']['debug']
    TESTING: bool = data['system']['testing']

    """server configuration"""
    SECRET_KEY: str = data['system']['secret_key']
    TIME_FORMAT_FILE = data['system']['time_format_file']
    TEMPLATES_AUTO_RELOAD: bool = True
    TEMPLATES_FOLDER = 'templates'
    APPLICATION_NAME = socket.gethostname()
    APPLICATION_USER = data['system']['application_user']
    APPLICATION_USER_GRP = data['system']['application_user_group']

    LOGGING_LEVEL = data['logging']['log_level']
    LOGGING_FORMAT = data['logging']['log_format']
    LOGGING_FILE_NAME = data['logging']['log_file_name']

    """server upload"""
    SERVER_UPLOAD_ENABLED: bool = data['server_upload']['enabled']
    SERVER_PAUSE_RETRY_UPLOAD: int = data['server_upload']['pause_retry']
    SERVER_NUM_RETRY_UPLOAD: int = data['server_upload']['num_retry']
    SERVER_FOLDER_UPLOAD: str = data['server_upload']['folder']
    SERVER_UPLOAD: str = data['server_upload']['server_name']
    SERVER_USER_UPLOAD: str = data['server_upload']['user']
    SERVER_PASS_UPLOAD: str = data['server_upload']['password']
    SERVER_FTP_ENABLED: bool = data['server_upload']['ftp_enabled']
    SERVER_SMB_ENABLED: bool = data['server_upload']['smb_enabled']
    SERVER_TIME_UPLOAD = data['server_upload']['upload_time']
    SERVER_DELETE_AFTER_UPLOAD_ENABLED: bool = data['server_upload']['delete_after_upload']

    """Video Configuration"""
    VID_DURATION: int = data['video']['duration']
    VID_PREFIX: str = data['video']['video_prefix']
    VID_RES_X: int = data['video']['x_resolution']
    VID_RES_Y: int = data['video']['y_resolution']
    VID_FRAMES: int = data['video']['frames_per_sec']
    VID_FOURCC: str = data['video']['fourcc']
    VID_FORMAT: str = data['video']['video_format']
    VID_SOUND_FORMAT: str = data['video']['output_sound_format']
    VID_ENDINGS = data['video']['output_video_format']
    VID_LABEL_FORMAT: str = data['video']['video_label_format']
    VID_ROTATE_ENABLED: bool = data['video']['video_rotation_enabled']

    """Replay configuration"""
    REPLAY_FRAMES_PER_SEC = data['replay']['frames_per_sec']
    REPLAY_PATH: str = data['replay']['output_path']
    REPLAY_ENABLED: bool = data['replay']['enabled']
    REPLAY_SCREENSHOT_PATH: str = data['replay']['path_snapshots']
    REPLAY_INTERVAL: int = data['replay']['interval']
    REPLAY_PREFIX_VID: str = data['replay']['prefix']
    REPLAY_DAYS: int = data['replay']['replay_interval']

    """Picture configuration"""
    PICTURE_PREFIX: str = socket.gethostname() + '_'
    PICTURE_ENDING: str = 'jpg'
    PICTURE_LATEST_RES_X = '1280'
    PICTURE_LATEST_RES_Y = '720'

    """Video analytics configuration"""
    VID_ANALYSER_TIME_RUN = '02:00'
    VID_ANALYSER_ENABLED: bool = False

    """LandingPage Configuration"""
    NAME_BIRD = ''
    DATE_CHICK: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_EGG: datetime  = datetime.strptime('01.01.1900', '%d.%m.%Y')
    FIRST_VISIT: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')
    DATE_LEAVE: datetime = datetime.strptime('01.01.1900', '%d.%m.%Y')

    """motion handling configuration"""
    MOTION_HANDLING_ENABLED: bool = data['motion_detection']['enabled']
    MOTION_HANDLING_SENSITIVITY: int = data['motion_detection']['sensitivity']

    """database configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = data['database']['uri']
    SQLALCHEMY_DATABASE_USER = data['database']['user']
    SQLALCHEMY_DATABASE_PASSW = data['database']['password']

    """folder structure"""
    for folder in data['folder_structure']:
        if folder == "output_folder":
            OUTPUT_FOLDER = create_folder_name(data['folder_structure']['output_folder'])
        elif folder == "media_folder":
            DATABASE_FOLDER = create_folder_name(data['folder_structure']['media_folder'])
        elif folder == "database_folder":
            DATABASE_FOLDER = create_folder_name(data['folder_structure']['database_folder'])
        elif folder == "replay_folder":
            REPLAY_FOLDER = create_folder_name(data['folder_structure']['replay_folder'])
        elif folder == "picture_folder":
            PICTURE_FOLDER = create_folder_name(data['folder_structure']['picture_folder'])
        elif folder == "video_folder":
            VIDEO_FOLDER = create_folder_name(data['folder_structure']['video_folder'])
        elif folder == "screenshot_folder":
            SCREENSHOT_FOLDER = create_folder_name(data['folder_structure']['screenshot_folder'])
        elif folder == "vid_analyser_folder":
            NO_DETECT_FOLDER = create_folder_name(data['folder_structure']['vid_analyser_folder'])
        elif folder == "picture_personas":
            PERSONAS_FOLDER = create_folder_name(data['folder_structure']['picture_personas'])
        elif folder == "logfile_location":
            LOGGING_FILE_FOLDER = create_folder_name(data['folder_structure']['log_file_folder'])

    FLASK_DEBUG = 1
    FLASK_ENV = 'development'
