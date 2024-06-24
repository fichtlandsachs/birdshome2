import datetime
import io
import os
import pathlib
import sqlite3
import threading
import imutils as imutils
import numpy as np

from application.forms.admin_form import AdminForm
from application.handler.database_hndl import DBHandler

try:
    from uwsgidecorators import *
    import uwsgi
except:
    pass
import cv2

from flask import render_template, Response, g, request, redirect, url_for
from application import create_app, constants, write_Configuration_db

app = create_app()

with app.app_context():
    from application.handler.motion_handler import Motion_Handler
    from application.handler.screen_shoot_handler import ScreenShotHandler
    from application.handler.fileUploader import FileUploader
    from application.handler.fileSorter import FileSorter
    # Erzeugen der Instanz für die Aufnahme
    #
    # da die Kamera für die Aufnahme für andere Programme dann gesperrt
    # ist es erforderlich die Instanz an die weiteren Funktionen weiterzugeben
vc = app.config.get(constants.VIDEO_CAPTURE_INST)
if vc is None:
    vc = cv2.VideoCapture(0, cv2.CAP_V4L)
if vc.isOpened():
    app.logger.info("app: Video capture received")
    vc.set(cv2.CAP_PROP_FPS, int(app.config.get(constants.VID_FRAMES)))
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, int(app.config.get(constants.VID_RES_X)))
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, int(app.config.get(constants.VID_RES_Y)))
    app.config[constants.VIDEO_CAPTURE_INST] = vc
else:
    app.logger.info("app: Failed to receive Video capture")

videoFolder = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                           app.config.get(constants.VIDEO_FOLDER))
app.logger.info("app: Video folder set to {}".format(videoFolder))
pictureFolder = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                             app.config.get(constants.PICTURE_FOLDER))
app.logger.info("app: picture folder set to {}".format(pictureFolder))
replayFolder = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                            app.config.get(constants.REPLAY_FOLDER))
app.logger.info("app: replay folder set to {}".format(replayFolder))
DATABASE = app.config.get(constants.SQLALCHEMY_DATABASE_URI)
app.logger.info("app: database connection set to {}".format(DATABASE))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        if db is None:
            app.logger.error('app: database not available in method get_db')
        else:
            app.logger.info('app: created a database connection')
    return db


def create_create_bg_task():
    uwsgi_thread = threading.Thread(target=uwsgi_task)
    thread_replay = threading.Thread(target=replay_task)
    thread_file_upload = threading.Thread(target=fileUpload_task)
    thread_file_sorter = threading.Thread(target=filesorter_task)

    uwsgi_thread.start()
    app.logger.info("app: uwsgi task started")
    thread_replay.start()
    app.logger.info("app: replay thread started")
    thread_file_upload.start()
    app.logger.info("app: File upload thread started")
    thread_file_sorter.start()
    app.logger.info("app: File sorter thread started")


def replay_task():
    with app.app_context():
        ScreenShotHandler(vc).start_Replay()


def filesorter_task():
    with app.app_context():
        FileSorter().analyseFiles()


def fileUpload_task():
    with app.app_context():
        FileUploader().uploadFiles()


def uwsgi_task():
    with app.app_context():
        Motion_Handler(vc).detect()


# Erzeugen eines Hintergrundtask, welcher die Kamera permanent überwacht und be Bewegungen eine Aufzeichnung startet
create_create_bg_task()


@app.route('/')
@app.route('/personas', methods=['GET', 'POST'])
def personas():
    with app.app_context():
        _db = DBHandler(app.config.get(constants.SQLALCHEMY_DATABASE_URI))
    if request.method == 'GET' or (request.method == 'POST' and len(request.form) == 0):
        first_visit = app.config.get(constants.FIRST_VISIT)
        date_eggs = app.config.get(constants.DATE_EGG)
        date_chick = app.config.get(constants.DATE_CHICK)
        date_leave = app.config.get(constants.DATE_LEAVE)
        name_bird = app.config.get(constants.NAME_BIRD)

    elif request.method == 'POST' and len(request.form) > 0:
        name_bird = request.form['name_bird']
        first_visit = request.form['first_visit']
        date_eggs = request.form['date_eggs']
        date_chick = request.form['date_chick']
        date_leave = request.form['date_leave']

        if name_bird is not None or name_bird != '':
            _db.createUpdateConfigEntry(constants.NEST_CONFIG, constants.NAME_BIRD, name_bird)
            app.config[constants.NAME_BIRD] = name_bird
        if first_visit is not None or first_visit != '':
            _db.createUpdateConfigEntry(constants.NEST_CONFIG, constants.FIRST_VISIT, first_visit)
            app.config[constants.FIRST_VISIT] = first_visit
        if date_eggs is not None or date_eggs != '':
            _db.createUpdateConfigEntry(constants.NEST_CONFIG, constants.DATE_EGG, date_eggs)
            app.config[constants.DATE_EGG] = date_eggs
        if date_chick is not None or date_chick != '':
            _db.createUpdateConfigEntry(constants.NEST_CONFIG, constants.DATE_CHICK, date_chick)
            app.config[constants.DATE_CHICK] = date_chick
        if date_leave is not None or date_leave != '':
            _db.createUpdateConfigEntry(constants.NEST_CONFIG, constants.DATE_LEAVE, date_leave)
            app.config[constants.DATE_LEAVE] = date_leave
    folder_personas = str(os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                                       app.config[constants.PERSONAS_FOLDER]) + '/personas' + '.' + str(
        app.config.get(constants.PICTURE_ENDING)))
    pic_personas = str(
        pathlib.Path(folder_personas).relative_to(app.root_path))
    _db.close()
    return render_template("personas.html", num_visits_today=0, last_visit=0,
                           pic_personas=pic_personas, first_visit=first_visit, date_eggs=date_eggs,
                           date_chick=date_chick, date_leave=date_leave, name_bird=name_bird)


# Livestream für die Website
@app.route('/stream')
def stream():
    return render_template('streaming.html')


# Route zum aufnehmen eines Videos direkt über die Website
@app.route('/capture')
def capture():
    # Define the codec and create VideoWriter object
    with app.app_context():
        m_handler = Motion_Handler(vc)
        m_handler.startRecording()
    return redirect(url_for('stream'))


@app.route('/slideshow')
def slideshow():
    # Auslesen der Bilder im Applikationsverzeichnis und Anzeige auf der Webseite
    # die Konfiguration des Verzeichnisses erfolgt in der config.py

    pictures = []

    pic_path = str(os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                app.config.get(constants.PICTURE_FOLDER)))
    pictures_list = list(
        sorted(pathlib.Path(pic_path).glob('*' + str(app.config.get(constants.PICTURE_ENDING))), key=os.path.getmtime))
    for pic in pictures_list:
        pict = [pic.name, str(pic.relative_to(app.root_path))]
        pictures.append(pict)
    return render_template('slideshow.html', pictures=pictures)


def gen():
    # """Video streaming generator function."""
    vc_instance = app.config.get(constants.VIDEO_CAPTURE_INST)
    if vc_instance is None or not vc_instance.isOpened():
        vc_instance = cv2.VideoCapture(0)
    while True:
        read_return_code, frame = vc_instance.read()
        if read_return_code:
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
            if app.config.get(constants.VID_ROTATE_ENABLED) == 'True':
                frame = imutils.rotate(frame, 180)
            _draw_label(frame, datetime.datetime.now().strftime(constants.DATETIME_FORMAT), (20, 20))

            encode_return_code, image_buffer = cv2.imencode('.' + str(app.config.get(constants.PICTURE_ENDING)), frame)
            io_buf = io.BytesIO(image_buffer)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + io_buf.read() + b'\r\n')


def _draw_label(img, text, pos):
    # zeichnen des Labels in das Bild
    # das Bild die Position und der einzufügende Text werden als Parameter übergeben
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = .4
    color = (255, 255, 255)
    cv2.putText(img, text, pos, font_face, scale, color, 1, cv2.LINE_AA)


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/cam')
def cam():
    fileName_short = app.config.get(constants.PICTURE_PREFIX) + datetime.datetime.now().strftime(
        app.config.get(constants.TIME_FORMAT_FILE)) + '.' + str(app.config.get(constants.PICTURE_ENDING))
    full_filename = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                 app.config.get(constants.PICTURE_FOLDER),
                                 fileName_short)
    _take_picture(full_filename)
    return redirect(url_for('slideshow'))


@app.route('/screenshot')
def screenshot():
    fileName_short = app.config.get(constants.PICTURE_PREFIX) + datetime.datetime.now().strftime(
        app.config.get(constants.TIME_FORMAT_FILE)) + '.' + str(
        app.config.get(constants.PICTURE_ENDING))
    full_filename = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                                 app.config.get(constants.SCREENSHOT_FOLDER),
                                 fileName_short)
    _take_picture(full_filename)
    return redirect(url_for('slideshow'))


# Aufnehmen eines Fotos
def _take_picture(fileName):
    frame = np.array((int(app.config.get(constants.VID_RES_X)), int(app.config.get(constants.VID_RES_Y)), 3),
                     dtype=np.uint8)
    check, frame = vc.read(frame)
    if check:
        _draw_label(frame, datetime.datetime.now().strftime(constants.DATETIME_FORMAT), (20, 20))
        image_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        cv2.imwrite(fileName, image_gray)


@app.route('/videoList', methods=['GET', 'POST'])
def videoList():
    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vid_path = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                            app.config.get(constants.VIDEO_FOLDER))
    vidDate = str(sel_datum.day) + str(format(sel_datum.month, '02')) + str(
        sel_datum.year)
    videos = getVidList(vidDate, vid_path)
    return render_template('videoshow.html', videos=videos, date_selection=sel_datum)


@app.route('/replayList', methods=['GET', 'POST'])
def replayList():
    videos = []
    vidList = list()

    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vid_path = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                            app.config.get(constants.REPLAY_PATH))
    for ending in app.config.get(constants.VID_ENDINGS):
        pattern = ending
        vidList.extend(list(sorted(pathlib.Path(vid_path).glob(pattern), key=os.path.getmtime, reverse=True)))

    for media in vidList:
        vid = [media.name, str(media.relative_to(app.root_path))]
        videos.append(vid)
    return render_template('replayshow.html', videos=videos, date_selection=sel_datum)


@app.route('/videoList_10001', methods=['GET', 'POST'])
def videoList_10001():
    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vid_path = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                            app.config.get(constants.VIDEO_FOLDER), 'detect', 'above_10000')
    vidDate = str(sel_datum.day) + str(format(sel_datum.month, '02')) + str(
        sel_datum.year)
    videos = getVidList(vidDate, vid_path)
    return render_template('vidList_10001.html', videos=videos, date_selection=sel_datum)


@app.route('/videoList_5001', methods=['GET', 'POST'])
def videoList_5001():
    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vid_path = os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                            app.config[constants.VIDEO_FOLDER], 'detect', 'less_10000')
    vidDate = str(sel_datum.day) + str(format(sel_datum.month, '02')) + str(
        sel_datum.year)
    videos = getVidList(vidDate, vid_path)
    return render_template('vidList_5001.html', videos=videos, date_selection=sel_datum)


@app.route('/videoList_5000', methods=['GET', 'POST'])
def videoList_5000():
    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vid_path = os.path.join(app.root_path, app.config[constants.OUTPUT_FOLDER],
                            app.config[constants.VIDEO_FOLDER], 'detect', 'less_5000')
    vidDate = str(sel_datum.day) + str(format(sel_datum.month, '02')) + str(
        sel_datum.year)
    videos = getVidList(vidDate, vid_path)
    return render_template('vidList_5000.html', videos=videos, date_selection=sel_datum)


@app.route('/videoList_noDetect', methods=['GET', 'POST'])
def videoList_noDetect():
    vid_path = os.path.join(app.root_path, app.config.get(constants.OUTPUT_FOLDER),
                            app.config.get(constants.NO_DETECT_FOLDER))
    if request.method == 'POST':
        form_datum = request.form.get('dateFiles')
        sel_datum = datetime.datetime.strptime(form_datum, constants.DATEFORMATE_FILE_SEL)
    else:
        sel_datum = datetime.datetime.today()

    vidDate = str(sel_datum.day) + str(format(sel_datum.month, '02')) + str(
        sel_datum.year)
    videos = getVidList(vidDate, vid_path)
    return render_template('vidList_Nodetect.html', videos=videos, date_selection=sel_datum)


def getVidList(vidDate, vidPath):
    videos = []
    vidList = list()
    for ending in app.config[constants.VID_ENDINGS]:
        pattern = '*' + vidDate + ending
        vidList.extend(list(sorted(pathlib.Path(vidPath).glob(pattern), key=os.path.getmtime)))

    for media in vidList:
        vid = [media.name, str(media.relative_to(app.root_path))]
        videos.append(vid)
    return videos


def _cleanFolder(folder, pattern):
    if os.path.exists(folder):
        for file_object in os.listdir(folder):
            file_object_path = os.path.join(folder, file_object)
            if file_object.startswith(pattern):
                if os.path.isfile(file_object_path) or os.path.islink(file_object_path):
                    os.unlink(file_object_path)
    else:
        os.makedirs(folder)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db != None:
        db.close()


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    adminForm = AdminForm()
    if request.method == 'POST':
        appConfig = [
            [constants.VID_DURATION, 'duration_vid', 'int'],
            [constants.VID_RES_X, 'vid_res_x', 'int'],
            [constants.VID_RES_Y, 'vid_res_y', 'int'],
            [constants.MOTION_HANDLING_SENSITIVITY, 'sensitivity', 'int'],
            [constants.VID_PREFIX, 'prefix_vid', 'str'],
            [constants.REPLAY_ENABLED, 'replay_enabled', 'bool'],
            [constants.REPLAY_INTERVAL, 'replay_interval', 'int'],
            [constants.REPLAY_FRAMES_PER_SEC, 'frames_per_sec_replay', 'int'],
            [constants.REPLAY_DAYS, 'replay_days', 'int'],
            [constants.SERVER_UPLOAD_ENABLED, 'upload_enabled', 'bool'],
            [constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED, 'delete_enabled', 'bool'],
            [constants.SERVER_NUM_RETRY_UPLOAD, 'num_retry_upload', 'int'],
            [constants.SERVER_PAUSE_RETRY_UPLOAD, 'pause_retry_upload', 'int'],
            [constants.SERVER_UPLOAD, 'server_upload', 'str'],
            [constants.SERVER_FOLDER_UPLOAD, 'folder_upload', 'str'],
            [constants.SERVER_TIME_UPLOAD, 'time_upload', 'date'],
            [constants.PICTURE_ENDING, 'pic_ending', 'str'],
            [constants.PICTURE_PREFIX, 'prefix_pic', 'str'],
            [constants.SERVER_USER_UPLOAD, 'user_upload', 'str'],
            [constants.SERVER_PASS_UPLOAD, 'password_upload', 'str'],
            [constants.SERVER_SMB_ENABLED, 'radio_ftp', 'bool'],
            [constants.VID_ANALYSER_ENABLED, 'radio_ftp', 'bool'],
            [constants.VID_ANALYSER_TIME_RUN, 'time_vid_sorter', 'date'],
            [constants.VID_ANALYSER_ENABLED, 'vid_sorter_enabled', 'bool'],
            [constants.VID_ROTATE_ENABLED, 'vid_drehen_enabled', 'bool'],
            [constants.MOTION_HANDLING_ENABLED, 'motion_handling_enabled', 'bool']
        ]

        for appConfigEntry in appConfig:

            if appConfigEntry[0][-8:] == '_ENABLED' and request.form.get(appConfigEntry[1]) is None:
                app.config[appConfigEntry[0]] = False
            elif appConfigEntry[0][-8:] == '_ENABLED' and request.form.get(appConfigEntry[1]) != None:
                app.config[appConfigEntry[0]] = True
            elif appConfigEntry[0][:3] == 'SMB':
                if request.form.get('radio_ftp') == 'ftp_upload':
                    app.config[constants.SERVER_SMB_ENABLED] = False
                    app.config[constants.SERVER_FOLDER_UPLOAD] = False
                    app.config[constants.SERVER_FTP_ENABLED] = True
                elif request.form.get('radio_ftp') == 'folder_upload':
                    app.config[constants.SERVER_SMB_ENABLED] = False
                    app.config[constants.SERVER_FOLDER_UPLOAD] = True
                    app.config[constants.SERVER_FTP_ENABLED] = False
                elif request.form.get('radio_ftp') == 'remoteFolder_upload':
                    app.config[constants.SERVER_SMB_ENABLED] = True
                    app.config[constants.SERVER_FOLDER_UPLOAD] = False
                    app.config[constants.SERVER_FTP_ENABLED] = False
            else:
                if request.form.get(appConfigEntry[1]) != None and appConfigEntry[2] != 'int':
                    app.config[appConfigEntry[0]] = request.form.get(appConfigEntry[1])
                elif request.form.get(appConfigEntry[1]) != None and appConfigEntry[2] == 'int':
                    app.config[appConfigEntry[0]] = int(float(request.form.get(appConfigEntry[1])))
                else:
                    continue
        if not app.config[constants.REPLAY_ENABLED]:
            clearPathScreenShots()
        write_Configuration_db(_app=app)

    if app.config.get(constants.VID_DURATION) is None:
        adminForm.duration_vid.data = int(0)
        adminForm.duration_vidVal.data = int(0)
    else:
        adminForm.duration_vid.data = int(float(app.config[constants.VID_DURATION]))
        adminForm.duration_vidVal.data = int(float(app.config[constants.VID_DURATION]))
    if app.config[constants.VID_RES_X] is None:
        adminForm.vid_res_x.data = int(0)
    else:
        adminForm.vid_res_x.data = int(app.config[constants.VID_RES_X])
    if app.config[constants.VID_RES_Y] is None:
        adminForm.vid_res_y.data = int(0)
    else:
        adminForm.vid_res_y.data = int(app.config[constants.VID_RES_Y])
    if app.config[constants.MOTION_HANDLING_SENSITIVITY] is None:
        adminForm.sensitivity.data = int(0)
        adminForm.sensitivityVal.data = int(0)
    else:
        adminForm.sensitivity.data = int(float(app.config[constants.MOTION_HANDLING_SENSITIVITY]))
        adminForm.sensitivityVal.data = int(float(app.config[constants.MOTION_HANDLING_SENSITIVITY]))
    if app.config[constants.REPLAY_INTERVAL] is None:
        adminForm.replay_interval.data = int(0)
    else:
        adminForm.replay_interval.data = int(app.config[constants.REPLAY_INTERVAL])
    if app.config[constants.REPLAY_DAYS] is None:
        adminForm.replay_days.data = int(0)
    else:
        adminForm.replay_days.data = int(app.config[constants.REPLAY_DAYS])
    if app.config[constants.REPLAY_FRAMES_PER_SEC] is None:
        adminForm.frames_per_sec_replay.data = int(0)
    else:
        adminForm.frames_per_sec_replay.data = int(app.config[constants.REPLAY_FRAMES_PER_SEC])
    if app.config[constants.SERVER_NUM_RETRY_UPLOAD] is None:
        adminForm.num_retry_upload.data = int(0)
    else:
        adminForm.num_retry_upload.data = int(app.config[constants.SERVER_NUM_RETRY_UPLOAD])

    if app.config[constants.SERVER_PAUSE_RETRY_UPLOAD] is None:
        adminForm.pause_retry_upload.data = int(0)
    else:
        adminForm.pause_retry_upload.data = int(app.config[constants.SERVER_PAUSE_RETRY_UPLOAD])

    if app.config[constants.SERVER_USER_UPLOAD] is None:
        adminForm.user_upload.data = ''
    else:
        adminForm.user_upload.data = app.config[constants.SERVER_USER_UPLOAD]

    if app.config[constants.SERVER_PASS_UPLOAD] is None:
        adminForm.password_upload.data = ''
    else:
        adminForm.password_upload.data = app.config[constants.SERVER_PASS_UPLOAD]

    adminForm.prefix_vid.data = app.config[constants.VID_PREFIX]

    if app.config[constants.SERVER_DELETE_AFTER_UPLOAD_ENABLED] == 'True':
        adminForm.delete_enabled.data = True
    else:
        adminForm.delete_enabled.data = False

    if app.config[constants.REPLAY_ENABLED] == 'True':
        adminForm.replay_enabled.data = True
    else:
        adminForm.replay_enabled.data = False

    if app.config[constants.SERVER_UPLOAD_ENABLED] == 'True':
        adminForm.upload_enabled.data = True
    else:
        adminForm.upload_enabled.data = False
    if app.config[constants.VID_ROTATE_ENABLED] == 'True':
        adminForm.vid_drehen_enabled.data = True
    else:
        adminForm.vid_drehen_enabled.data = False
    if app.config[constants.VID_ANALYSER_ENABLED] == 'True':
        adminForm.vid_sorter_enabled.data = True
    else:
        adminForm.vid_sorter_enabled.data = False
    adminForm.server_upload.data = app.config[constants.SERVER_UPLOAD]
    adminForm.folder_upload.data = app.config[constants.SERVER_FOLDER_UPLOAD]
    adminForm.time_upload.data = datetime.datetime.strptime(app.config[constants.SERVER_TIME_UPLOAD],
                                                            constants.SERVER_DATETIME_FORMAT).time()
    adminForm.time_vid_sorter.data = datetime.datetime.strptime(app.config[constants.VID_ANALYSER_TIME_RUN],
                                                                constants.SERVER_DATETIME_FORMAT).time()
    adminForm.prefix_pic.data = app.config[constants.PICTURE_PREFIX]
    adminForm.pic_ending.data = app.config[constants.PICTURE_ENDING]

    if adminForm.validate_on_submit():
        return redirect(url_for("admin"))
    return render_template(
        "admin_new.html",
        form=adminForm,
        template="form-template"
    )


def clearPathScreenShots():
    screenShots = list()
    pattern = '*.' + app.config[constants.PICTURE_ENDING]
    screen_path = app.config[constants.REPLAY_SCREENSHOT_PATH]
    screenShots.extend(list(sorted(pathlib.Path(screen_path).glob(pattern), key=os.path.getmtime,
                                   reverse=True)))
    for screen in screenShots:
        os.remove(screen)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5000', debug=True, use_reloader=False)
