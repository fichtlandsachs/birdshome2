import datetime
import threading
import cv2
import flask
import imutils

from application import constants


def _draw_label(img, text, pos):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = .4
    color = (255, 255, 255)

    cv2.putText(img, text, pos, font_face, scale, color, 1, cv2.LINE_AA)


class VideoRecorder(threading.Thread):

    def __init__(self, filename: str, recording: datetime, app: flask.app, vc: cv2.VideoCapture):
        threading.Thread.__init__(self)
        self.open: bool = True
        self.video_cap: cv2.VideoCapture = vc
        self.fileName: str = filename
        self.vidFrames = []
        self.frame = []
        self.vid_Out = None
        self.endTime: datetime = recording
        self.vid_duration: int = app.config.get(constants.VID_DURATION)
        self.label_format: str = app.config.get(constants.VID_LABEL_FORMAT)
        self.fourcc: str = app.config.get(constants.VID_FOURCC)
        self.vid_Height: int = app.config.get(constants.VID_RES_Y)
        self.vid_Width: int = app.config.get(constants.VID_RES_X)
        self.vid_drehen: bool = app.config[constants.VID_ROTATE_ENABLED]

    def run(self):

        while self.endTime > datetime.datetime.now():
            check, frame = self.video_cap.read()
            if check:
                if self.vid_drehen:
                    frame = imutils.rotate(frame, 180)
                _draw_label(frame, datetime.datetime.now().strftime(self.label_format), (20, 20))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                vid_frame = [gray, [datetime.datetime.now().strftime(self.label_format)]]
                self.vidFrames.append(vid_frame)
            cv2.waitKey(33)

        i = len(self.vidFrames)
        video_frames_num = i / self.vid_duration
        fourcc = cv2.VideoWriter.fourcc(*'avc1')
        vid_Out = cv2.VideoWriter(self.fileName, fourcc, video_frames_num, (1280, 720), False)
        for curr_viFrame in self.vidFrames:
            frame = curr_viFrame[0]
            vid_Out.write(frame)
        # vid_Out.release()

    def stop(self):
        "Finishes the video recording therefore the thread too"
        if self.open:
            self.open = False
            self.vidFrames.clear()
