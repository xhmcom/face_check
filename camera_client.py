# coding=utf-8
# __author__ = 'xhm'
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import cv2
import face_check
import threading
import traceback
import db_helper
import datetime
import logging
import time
from PIL import Image, ImageDraw, ImageFont
import numpy
import socket

mutex = threading.Lock()
frame_list = []
realname = ''

def frame_read(camera_ad=0):
    """
    摄像头启动，记录帧
    Args:
        camera_ad: 摄像头地址

    Returns:

    """

    cap = cv2.VideoCapture(camera_ad)
    global realname
    try:
        while True:
            time.sleep(0.01)
            ret, frame = cap.read()
            if ret:
                if mutex.acquire():
                    global frame_list
                    frame_list.append(frame)
                    mutex.release()
                
                if realname != '':
                    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    zh_font = ImageFont.truetype('DroidSansFallbackFull.ttf', 40)
                    en_font = ImageFont.truetype('DejaVuSans-BoldOblique.ttf', 40)
                    fillcolor = (255, 0, 0)
                    pos = (30, 30)
                    if not isinstance(realname, unicode):
                        realname = realname.decode('utf-8')
                    draw = ImageDraw.Draw(img_pil)
                    if realname == 'unknown':
                        font = en_font
                    else:
                        font = zh_font
                    draw.text(pos, realname, font=font, fill=fillcolor)
                    frame = cv2.cvtColor(numpy.asarray(img_pil), cv2.COLOR_RGB2BGR)
                cv2.imshow('Video', frame)
            else:
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(camera_ad)
            c = cv2.waitKey(1)
            if c == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def frame_check():
    """
    拉取帧进行人脸签到
    Returns:

    """
    global realname
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect(('192.168.0.141', 8080))
    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
    while True:
        time.sleep(0.01)
        frame = None
        flagframe = False
        if mutex.acquire():
            global frame_list
            if frame_list:
                frame = frame_list[-1]
                flagframe = True
            frame_list = []
            mutex.release()
        if flagframe:
            print("sending frame...")
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(imgencode)
            string_data = data.tostring()
            sock.send(str(len(string_data)).ljust(16))
            sock.send(string_data)
            print("send finish...")
            realname = sock.recv(64)
            print("receive realname: " + str(realname))
    sock.close()


def main():
    """
    main函数 两个线程
    Returns:

    """
    t_read = threading.Thread(target=frame_read)
    t_read.start()

    t_check = threading.Thread(target=frame_check)
    t_check.start()

if __name__ == '__main__':
    main()
