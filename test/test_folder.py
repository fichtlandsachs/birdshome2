import datetime
import glob
import os
import pathlib
import time

if __name__ == "__main__":
    vidList = list()
    videos = []
    first_visit = datetime.datetime.today().strftime('%d.%m.%YT%H:%M:%S')
    endings = ['*.avi', '*.mp4']
    list_of_files = glob.glob('/etc/birdshome/application/static/media/videos/*.avi')
    latest_file = max(list_of_files, key=os.path.getctime)
    fileStat = os.stat(latest_file).st_ctime
    latest_file_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(os.stat(latest_file).st_ctime))
    num_filesToday = len(glob.glob(
        '/etc/birdshome/application/static/media/videos/*' + str(datetime.datetime.today().day) + str(
            format(datetime.datetime.today().month, '02')) + str(datetime.datetime.today().year) + '*.mp4'))
    num_files = len(glob.glob('/etc/birdshome/application/static/media/videos/*.mp4'))
    vid_path = os.path.join(os.path.dirname(__file__), '../application/static', 'media/videos')
    vidDate = str(datetime.datetime.today().day) + str(format(datetime.datetime.today().month, '02')) + str(
        datetime.datetime.today().year)
    for ending in endings:
        pattern = '*' + vidDate + ending
        vidList.extend(list(sorted(pathlib.Path(vid_path).glob(pattern), key=os.path.getmtime)))
    for media in vidList:
        vid = [media.name, str(media.relative_to(os.path.join(os.path.dirname(__file__), '../application')))]
        videos.append(vid)
    print()
