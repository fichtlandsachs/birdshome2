import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from application.models import appConfig


class DBHandler:
    def __init__(self, dbUrl):
        # Gets or creates a logger
        self.logger = None
        self.file_handler = None
        self.dbURL = dbUrl
        self.session = None
        self.conn = None
        # add file handler to logger
        self.open()

    def close(self):
        self.session.close()
        self.conn.close()
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()

    def open(self):
        try:
            self.logger = logging.getLogger(__name__)

            # set log level
            self.logger.setLevel(logging.ERROR)

            # define file handler and set formatter
            self.file_handler = logging.FileHandler('db_logfile.log')
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
            self.file_handler.setFormatter(formatter)
            self.logger.addHandler(self.file_handler)
            engine = create_engine(self.dbURL, poolclass=NullPool, connect_args={'check_same_thread': False})
            engine.dispose()
            self.conn = engine.connect()
            self.conn.detach()
            Session = sessionmaker(bind=engine)
            self.session = Session()
        except Exception as e:
            self.logger.error(e.args[0])
            self.close()

    def getConfigEntry(self, app_area, config_key):
        try:
            if self.checkConfigEntryExists(app_area, config_key):
                self.open()
                entry = self.session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
                self.close()
                if entry is not None:
                    if config_key[-8:] == '_ENABLED' and entry.config_value == '1':
                        entry.config_value = True
                    if config_key[-8:] == '_ENABLED' and entry.config_value == '0':
                        entry.config_value = False
                    return entry.config_value
                else:
                    return None
            else:
                return None
        except Exception as e:
            self.logger.error('failed to read config entry ' + app_area + '' + config_key + '' + e.args[0])
            self.close()

    def checkConfigEntryExists(self, app_area, config_key):
        try:
            self.open()
            entry = self.session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
            self.close()
            if entry is None:
                return False
            else:
                return True
        except Exception as e:
            self.logger.error('failed to read config entry ' + app_area + '' + config_key + '' + e.args[0])
            self.close()

    def getAllConfigEntriesForArea(self, app_area):
        try:
            self.open()
            entries = self.session.query(appConfig).filter_by(config_area=app_area).all()
            self.close()
            return entries
        except Exception as e:
            self.logger.error('failed to read config entry ' + app_area + '' + e.args[0])
            self.close()

    def createUpdateConfigEntry(self, app_area, config_key, config_value):
        try:
            self.open()
            if self.checkConfigEntryExists(app_area, config_key):
                entry = self.session.query(appConfig).filter_by(config_area=app_area, config_key=config_key).first()
                if entry != None:
                    entry.config_value = config_value
                    self.session.add(entry)
            else:
                self.open()
                self.logger.info('create config record: ' + app_area + ' ' + config_key)
                configRecord = appConfig()
                configRecord.config_area = app_area
                configRecord.config_key = config_key
                configRecord.config_value = config_value
                self.session.add(configRecord)
            self.session.commit()
            self.close()
        except Exception as e:
            self.logger.error('failed to update config entry ' + app_area + '' + config_key + '' + e.args[0])
            self.close()

    def createUpdateConfigEntryBulk(self, values: list):
        self.logger.info('Create Bulb Update for Config Entries')
        self.open()
        for value in values:
            configRecord = appConfig()
            configRecord.config_area = value[0]
            configRecord.config_key = value[1]
            configRecord.config_value = str(value[2])
            self.session.merge(configRecord)
        self.session.commit()
        self.close()
