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

import faulthandler  # 打印段错误报错细节
faulthandler.enable()

mutex = threading.Lock()  # 互斥锁
frame_list = []  # 帧序列
realname = ''  # 记录实时检测结果
face_session = dict()
face_session['timestamp'] = 0
face_session['username'] = 'unknown'

def frame_read(camera_ad=0):
    """
    摄像头启动，记录帧，输出检测结果到屏幕
    Args:
        camera_ad: 摄像头地址

    Returns:

    """

    cap = cv2.VideoCapture(camera_ad)
    global realname
    try:
        while True:
            time.sleep(0.001)  # 挂起防止cpu爆表
            ret, frame = cap.read()
            if ret:
                if mutex.acquire():
                    global frame_list
                    if len(frame_list) > 10:
                        frame_list = []  # 防止帧序列过长
                    frame_list.append(frame)
                    mutex.release()
                
                if realname != '':  # 绘制结果
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
                # frame = cv2.resize(frame, (1280, 960), interpolation=cv2.INTER_CUBIC)
                #cv2.namedWindow('Video', 0)
                cv2.imshow('Video', frame)
                cv2.moveWindow('Video', 0, 0)  # 移动窗口到左上角
            else:
                # 唤醒摄像头失败，重试
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
    获取帧进行人脸签到
    Returns:

    """
    db = db_helper.DBHelper()
    db_flag = db.connect_database()  # 连接数据库
    global realname
    keep_sql = 10000
    while True:
        time.sleep(0.001)
        n_frame = None
        if mutex.acquire():
            # 拿到帧后清空帧序列
            global frame_list
            if frame_list:
                n_frame = frame_list[-1]
            frame_list = []
            mutex.release()

        if n_frame is not None:
            keep_sql -= 1
            # 保持数据库长连接，用的隔段时间访问一次的方法。。。
            if keep_sql == 0:
                get_realname(db, 'xuhuanmin')
                keep_sql = 5000
                print('keep alive...')
            # 检测人脸
            face = face_check.FaceHandler()
            try:
                face.set_image(image=face_check.get_base64(n_frame), image_type='BASE64')
                try:
                    face_dt = face.face_detect()
                except:
                    face_dt = False
                
                if face_dt:
                    # show faces
                    print(time.time(), ' detected')
                    face_list = face.get_faces()

                    face_time, username = face.face_search()
                    print(face_time)
                    print(username)
                    if not db_flag:
                        db = db_helper.DBHelper()
                        db_flag = db.connect_database()
                    if username != 'unknown':
                        # 检测到有效人脸，写入数据库
                        realname = get_realname(db, username)
                        if username == face_session['username'] and \
                                                (face_time - face_session['timestamp']) < 10:
                            # 10秒内重复出现记录为同一个人
                            logging.warning("Same person")
                        else:
                            t_s = time.time()
                            insert_check(db, face_time, username)
                            t_e = time.time()
                            print("time: " + str(t_e-t_s))
                        face_session['username'] = username
                        face_session['timestamp'] = face_time
                    else:
                        realname = 'unknown'
                else:
                    realname = ''
                    print(time.time(), ' undetected')
                time.sleep(0.1)  # 挂起减小cpu压力
            except:
                traceback.print_exc()


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
    从数据库拿到对应username的中文姓名
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
    main函数 两个线程
    Returns:

    """
    print('start')
    t_read = threading.Thread(target=frame_read)
    t_read.start()

    t_check = threading.Thread(target=frame_check)
    t_check.start()

if __name__ == '__main__':
    main()
