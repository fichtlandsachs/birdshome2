import cv2

if __name__ == "__main__":
    vc = cv2.cv2.VideoCapture(0)
    vc.set(cv2.CAP_PROP_FPS, 30)
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    # vc.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    fourcc = 'avc1'
    videoFolder = '/etc/birdshome/application/static/media/videos'
    fourcc = cv2.cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3])
    vid_Out = cv2.cv2.VideoWriter('/etc/birdshome/application/static/media/videos/test.mp4', fourcc, 30, (640, 480),
                                  False)
    counter = 0

    while counter < 100:
        ret, frame = vc.read()
        if ret:
            gray = cv2.cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vid_Out.write(gray)
            counter = counter + 1

    vid_Out.release()
