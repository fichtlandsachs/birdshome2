import socket

import flask
import pysftp
from smb.SMBConnection import SMBConnection

from application import constants


class Connection_handler:
    def __init__(self, app: flask.app):
        self.app = app
        self.connection = None
        self.user = None
        self.password = None
        self.my_name = socket.gethostname()

    def get_configuration(self):
        if self.app.config.get(constants.SERVER_UPLOAD_ENABLED):
            self.user = self.app.config.get(constants.SERVER_USER_UPLOAD)
            self.password = self.app.config.get(constants.SERVER_PASS_UPLOAD)

        if self.user is not None or self.password is not None:
            return

    def get_connection(self):
        if self.app.config.get(constants.SERVER_SMB_ENABLED):
            self.app.logger.info('Connecting to SMB server')
            self.connection = SMBConnection(username=self.user, password=self.password, use_ntlm_v2=True,
                                            remote_name=self.app.config.get(constants.SERVER_NAME), is_direct_tcp=True)
            remote_ip = socket.gethostbyname(self.app.config.get(constants.SERVER_NAME))
            self.connection.connect(ip=remote_ip)
            if self.connection.onAuthFailed():
                self.app.logger.error(f'Connection to SMB server failed: {self.connection}')
                self.connection = None
            return self.connection

        if self.app.config.get(constants.SERVER_FTP_ENABLED):
            self.app.logger.info('Connecting to FTP server')
            try:
                self.connection = pysftp.Connection(host=self.app.config.get(constants.SERVER_NAME),
                                                    username=self.app.config.get(constants.SERVER_USER_UPLOAD),
                                                    password=self.app.config.get(constants.SERVER_PASS_UPLOAD),
                                                    port=self.app.config.get(constants.SERVER_PORT))
            except Exception as err:
                self.app.logger.error(f'Error connecting to FTP server: {err}''')
                raise Exception(err)

            return self.connection

    def upload_file(self, file_path):
        if self.app.config.get(constants.SERVER_FTP_ENABLED):
            remote_path = self.app.config.get(constants.SERVER_FOLDER_UPLOAD)
            self.connection.put(file_path, remote_path)
        if self.app.config.get(constants.SERVER_SMB_ENABLED) and self.connection.onAuthOK():
            file_obj = open(file_path, 'rb')
            self.connection.storeFile(service_name=self.app.config.get(constants.SERVER_FOLDER_UPLOAD),
                                      path=file_path,
                                      file_obj=file_obj)

    def disconnect(self):
        self.connection.close()
        self.app.logger.info(f'Disconnected from server{self.app.config.get(constants.SERVER_NAME)}')
