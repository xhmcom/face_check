# coding=utf-8
# __author__ = 'xhm'
import cv2
import face_check
import threading
import traceback
import db_helper
import datetime
import logging
import time


mutex = threading.Lock()
frame_list = []
face_session = dict()
face_session['timestamp'] = 0
face_session['username'] = 'unknown'
c0_rtmp = "rtmp://rtmp.open.ys7.com/openlive/f6a7eb05c5b645acb7821020bcf9b057.hd"
c0_ezopen = "ezopen://open.ys7.com/C69004173/1.hd.live"

def frame_read(camera_ad=c0_rtmp):
    """
    摄像头启动，记录帧
    Args:
        camera_ad: 摄像头地址

    Returns:

    """

    cap = cv2.VideoCapture(camera_ad)
    try:
        while True:
            time.sleep(0.001)
            ret, frame = cap.read()
            if ret:
                if mutex.acquire():
                    global frame_list
                    frame_list.append(frame)
                    mutex.release()
                #yield cv2.imencode('.jpg', frame)[1].tobytes()
                #cv2.imshow('Video', frame)
            else:
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(camera_ad)
    finally:
        cap.release()
        #cv2.destroyAllWindows()


def frame_check():
    """
    拉取帧进行人脸签到
    Returns:

    """
    db = db_helper.DBHelper()
    db_flag = db.connect_database()
    while True:
        time.sleep(0.001)
        n_frame = None
        if mutex.acquire():
            global frame_list
            if frame_list:
                n_frame = frame_list[-1]
            frame_list = []
            mutex.release()

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
                    if username != 'unknown' and db_flag:
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
                time.sleep(0.2)
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
