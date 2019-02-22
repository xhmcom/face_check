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

face_session = dict()
face_session['timestamp'] = 0
face_session['username'] = 'unknown'
c0_rtmp = "rtmp://rtmp.open.ys7.com/openlive/f6a7eb05ci5b645acb7821020bcf9b057.hd"

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: 
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def socket_server():
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.bind(('192.168.0.141', 8888))
    sk.listen(True)
    print('start server...')
    conn, address = sk.accept()
    print('connected...')
    while True:
        time.sleep(0.001)
        frame_length = recvall(conn, 16)
        string_data = recvall(conn, str(frame_length))
        data = numpy.fromstring(string_data, dtype='uint8')
        frame = cv2.imdecode(data, 1)
        realname = get_check_ret(frame)
        conn.send(realname)
    sk.close()


def get_check_ret(n_frame):
    """
    Returns:

    """
    db = db_helper.DBHelper()
    db_flag = db.connect_database()
    realname = ''
    if n_frame is not None:
        face = face_check.FaceHandler()
        try:
            face.set_image(image=face_check.get_base64(n_frame), image_type='BASE64')
            if face.face_detect():
                # show faces
                face_list = face.get_faces()
                face_time, username = face.face_search()
                print(face_time)
                print(username)
                if not db_flag:
                    db = db_helper.DBHelper()
                    db_flag = db.connect_database()
                if username != 'unknown':
                    realname = get_realname(db, username)
                    if username == face_session['username'] and \
                                            (face_time - face_session['timestamp']) < 10:
                        # 10秒内重复出现记录为同一个人
                        logging.warning("Same person")
                    else:
                        t_s = time.time()
                        insert_check(db, face_time, username)
                        t_e = time.time()
                        print ("time: " + str(t_e-t_s))
                    face_session['username'] = username
                    face_session['timestamp'] = face_time
                else:
                    realname = 'unknown'
            else:
                realname = ''
            time.sleep(0.1)
        except:
            traceback.print_exc()
    return realname


def insert_check(db, timestamp, username):
    """
    添加记录进数据库
    每个人每天最多两条记录
    Args:
        db:
        timestamp:
        username:

    Returns:

    """
    face_datetime = datetime.datetime.fromtimestamp(timestamp)
    face_date = face_datetime.strftime("%Y-%m-%d")
    face_time = face_datetime.strftime("%Y-%m-%d %H:%M:%S")

    ret = db.fetchall("""select *
                         from check_t
                         where checkInDate = %s
                         and userName = %s""", (face_date, username))
    if ret is None or len(ret) <= 1:
        db.execute("insert into check_t (userName, checkInDate, checkInTime) "
                   "values (%s, %s, %s)", (username, face_date, face_time))
    # 超过两条，更新最晚记录
    if len(ret) > 1:
        update_time = ret[1][3] if ret[0][3] < ret[1][3] else ret[0][3]
        update_str = update_time.strftime("%Y-%m-%d %H:%M:%S")
        db.execute("""update check_t set checkInTime = %s
                      where userName = %s and checkInTime = %s
                    """, (face_time, username, update_str))


def get_realname(db, username):
    """
    get real name from database
    Args:
        db:
        username:
    Returns:
        realname:
    """

    realname = db.fetchall("""select realName
                              from user_t
                              where userName = %s""", username)
    return realname[0][0]


def main():
    """
    Returns:

    """
    socket_server()

if __name__ == '__main__':
    main()
