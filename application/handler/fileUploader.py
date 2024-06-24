import datetime
from time import sleep
import os

import pathlib
import shutil, ftplib
from smb.SMBHandler import SMBConnection
from flask import current_app
import socket
from application import constants

app = current_app
app_logger = app.logger

class FileUploader:
    def __init__(self):
        self.server = None
        self.server_not_found = False
        self.ftp_enabled = False
        self.smb_enabled = False
        self.folder_enabled = False
        self.user_upload = ''
        self.user_password = ''
        self.path = None
        self.updateConfig()
        app_logger.debug(__name__ + ' initialized')

    def updateConfig(self):
        self.server = app.config[constants.SERVER_UPLOAD]
        self.user_upload = app.config[constants.SERVER_USER_UPLOAD]
        self.user_password = app.config[constants.SERVER_PASS_UPLOAD]
        self.smb_enabled = app.config[constants.SERVER_SMB_ENABLED]
        self.ftp_enabled = app.config[constants.SERVER_FTP_ENABLED]
        self.path = app.config[constants.SERVER_FOLDER_UPLOAD]
        app_logger.debug('configuration read from app')

    def check_Network(self):
        try:
            self.ip_adress = socket.gethostbyname(self.server)
        except Exception as e:
            self.server_not_found = True
            app_logger.debug(str(self.server)+' server not found')

    def uploadPhotos(self):
        photos = list()
        pattern = '*.jpg'
        photo_path = os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                                  app.config[constants.PICTURE_FOLDER])
        photos.extend(list(sorted(pathlib.Path(photo_path).glob(pattern), key=os.path.getmtime,
                                  reverse=True)))
        app_logger.debug(str(len(photos)) + ' photos found for upload')
        for photo in photos:
            if self.smb_enabled:
                self.upload_file_via_smb(photo, app.config[constants.PICTURE_FOLDER])
            elif self.ftp_enabled:
                app_logger.debug('using ftp for upload')
                self.upload_file_via_ftp(photo, app.config[constants.PICTURE_FOLDER])
                app_logger.debug('ftp upload done')
            if self.folder_enabled:
                app_logger.debug('move file to folder')
                self.copyFileToFolder(photo, app.config[constants.PICTURE_FOLDER])
                app_logger.debug('file upload done')

    def uploadVideos(self):
        videos = list()
        pattern = '*.avi'
        video_path = os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                                  app.config[constants.VIDEO_FOLDER])
        videos.extend(list(sorted(pathlib.Path(video_path).glob(pattern), key=os.path.getmtime,
                                  reverse=True)))
        app_logger.debug(str(len(videos)) + ' videos found for upload')
        for video in videos:
            if self.smb_enabled:
                self.upload_file_via_smb(video, app.config[constants.VIDEO_FOLDER])
            elif self.ftp_enabled:
                self.upload_file_via_ftp(video, app.config[constants.VIDEO_FOLDER])
            if self.folder_enabled:
                self.copyFileToFolder(video, app.config[constants.VIDEO_FOLDER])

    def uploadReplays(self):
        replays = list()
        pattern = '*.avi'
        replay_path = os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                                   app.config[constants.REPLAY_FOLDER])
        replays.extend(list(sorted(pathlib.Path(replay_path).glob(pattern), key=os.path.getmtime,
                                   reverse=True)))
        app_logger.debug(str(len(replays))+' replay files found in folder ' + replay_path)
        for replay in replays:
            if self.smb_enabled:
                self.upload_file_via_smb(replay, app.config[constants.REPLAY_FOLDER])
            elif self.ftp_enabled:
                self.upload_file_via_ftp(replay, app.config[constants.REPLAY_FOLDER])
            if self.folder_enabled:
                self.copyFileToFolder(replay, app.config[constants.REPLAY_FOLDER])

    def copyFileToFolder(self, file, folderMedia):
        app_logger.debug('copy files to Folder used found for upload')
        folder_final = '/'
        folderStruct = app.config[constants.SERVER_FOLDER_UPLOAD].split('\\')
        for folder in folderStruct[1:]:
            folder_final = os.path.join(folder_final, folder)
        folderStruct = folderMedia.split('/')
        for folder in folderStruct:
            folder_final = os.path.join(folder_final, folder)
        file_remote = folder_final + '/' + file.name
        try:
            shutil.copy(file, file_remote)
        except Exception as ioException:
            app_logger.error(ioException.args)

    def upload_file_via_ftp(self, file, folderMedia):
        app_logger.debug('ftp upload is used for upload')
        folder_final = '/'
        self.check_Network()
        if not self.server_not_found:
            ftp_server = ftplib.FTP(host=app.config[constants.SERVER_UPLOAD],
                              username=app.config[constants.SERVER_USER_UPLOAD],
                              passwd=app.config[constants.SERVER_PASS_UPLOAD])
            try:
                folderStruct = app.config[constants.FOLDER_UPLOAD].split('\\')
                for folder in folderStruct[1:]:
                    folder_final = os.path.join(folder_final, folder)

                folderStruct = folderMedia.split('/')
                for folder in folderStruct:
                    folder_final = os.path.join(folder_final, folder)
                file_remote = folder_final + '/' + file.name
                obj = open(file=file, mode='rb')

                ftp_server.storbinary(f"STOR {file_remote}", obj)
                ftp_server.cwd(folder_final)
                for fileName in ftp_server.nlst(file.name):
                    fhandle = open(fileName, 'wb')
                    if fhandle.tell() == obj.tell():
                        os.remove(file)
                ftp_server.quit()
            except Exception as ioError:
                app_logger.error(ioError.args)

    def upload_file_via_smb(self, file, folderMedia):
        app_logger.debug('using smb for upload')
        folder_final = '/'
        self.check_Network()
        if not self.server_not_found:
            conn = SMBConnection(username=app.config[constants.SERVER_USER_UPLOAD],
                                 password=app.config[constants.SERVER_PASS_UPLOAD],
                                 my_name=str(socket.gethostname()),
                                 remote_name=app.config[constants.SERVER_UPLOAD],
                                 domain='', use_ntlm_v2=True,
                                 sign_options=SMBConnection.SIGN_WHEN_SUPPORTED,
                                 is_direct_tcp=True)
            connResult = conn.connect(self.ip_adress, 139)
            if connResult:
                try:
                    folderStruct = app.config[constants.SERVER_FOLDER_UPLOAD].split('\\')
                    for folder in folderStruct[2:]:
                        folder_final = os.path.join(folder_final, folder)
                    service = folderStruct[1]
                    folderStruct = folderMedia.split('/')
                    for folder in folderStruct:
                        folder_final = os.path.join(folder_final, folder)
                    file_remote = folder_final + '/' + file.name
                    obj = open(file=file, mode='rb')

                    conn.storeFile(path=file_remote, file_obj=obj, service_name=service)
                    remoteFile = conn.listPath(service_name=service, path=folder_final, pattern=file.name)
                    if not remoteFile is None and obj.tell() == remoteFile[0].file_size \
                            and not app.config[constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED]:
                        os.remove(file)

                except Exception as ioError:
                    app_logger.error(ioError.args)

    def uploadFiles(self):
        while True:
            if app.config[constants.SERVER_UPLOAD_ENABLED]:
                if self.server != '':
                    self.check_Network()
                    if not self.server_not_found:
                        time_upload = app.config[constants.SERVER_TIME_UPLOAD].split(':')
                        time_now = datetime.datetime.now().time()
                        if int(time_upload[0]) <= time_now.hour and int(time_upload[1]) <= time_now.minute:
                            self.uploadPhotos()
                            self.uploadVideos()
                            self.uploadReplays()
                else:
                    app_logger.error('upload enabled but server not found')
            else:
                app_logger.debug('server upload not enabled')
            sleep(60)
