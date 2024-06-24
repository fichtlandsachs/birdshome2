# Webcam Motion Detector Test programm
# the program is called to verify the sensitivity an values whiles movements detected
# it constantly checks the camera for differences
# every 100 frames it changes the reference picture to avoid permanent detection

from time import sleep

import cv2

# importing datetime class from datetime library

# Assigning our static_back to None
static_back = None

# Capturing video
video = cv2.VideoCapture(-1)
video.set(cv2.CAP_PROP_FPS, 30)

count = 0
# Infinite while loop to treat stack of image as video
while True:
    # Reading frame(image) from video
    check, frame = video.read()

    # Initializing motion = 0(no motion)
    motion = 0

    # Converting color image to gray_scale image
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Converting gray scale image to GaussianBlur
    # so that change can be find easily
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # In first iteration we assign the value
    # of static_back to our first frame
    if static_back is None:
        static_back = gray
        continue
    if count == 100:
        static_back = gray
        count = 0
    # Difference between static background
    # and current frame(which is GaussianBlur)
    diff_frame = cv2.absdiff(static_back, gray)

    # If change in between static background and
    # current frame is greater than 30 it will show white color(255)
    thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
    thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

    # Finding contour of moving object
    _, cnts, _ = cv2.findContours(thresh_frame.copy(),
                                  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in cnts:
        print(str(cv2.contourArea(contour)))
        if cv2.contourArea(contour) < 400:
            continue
        motion = 1

        (x, y, w, h) = cv2.boundingRect(contour)
        # static_back = frame
        # making green rectangle arround the moving object
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        # Displaying image in gray_scale
    cv2.imshow("Gray Frame", gray)

    # Displaying the difference in currentframe to
    # the staticframe(very first_frame)
    cv2.imshow("Difference Frame", diff_frame)

    # Displaying the black and white image in which if
    # intensity difference greater than 30 it will appear white
    cv2.imshow("Threshold Frame", thresh_frame)
    # Displaying color frame with contour of motion of object
    cv2.imshow("Color Frame", frame)

    key = cv2.waitKey(1)
    sleep(0.33)
    count = count + 1
    # Appending time of motion in DataFrame

video.release()

# Destroying all the windows
cv2.destroyAllWindows()
