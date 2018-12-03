# coding=utf-8
# __author__ = 'xhm'

from aip import AipFace
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
c0_rtmp = "rtmp://rtmp.open.ys7.com/openlive/f6a7eb05c5b645acb7821020bcf9b057.hd"


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
            ret, frame = cap.read()
            if ret:
                if mutex.acquire():
                    global frame_list
                    frame_list.append(frame)
                    mutex.release()
                # cv2.circle(frame, (frame.shape[1] // 2, frame.shape[0] // 2), 180, (255, 255, 255), 2)
                cv2.imshow('Video', frame)
            c = cv2.waitKey(1)
            if c == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def frame_register():
    """

    Returns:

    """

    db = db_helper.DBHelper()
    db_flag = db.connect_database()

    while True:
        username = raw_input('username: ')
        realname = raw_input('姓名:')
        # angle 表示人脸的角度 0到4依次表示 mid, up, down, left, right
        angle = [0, 0, 0, 0, 0]
        while not (angle[0] > 0 and angle[1] > 0 and angle[2] > 0 and angle[3] > 0 and angle[4] > 0):

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
                        face_list = face.get_faces()
                        face_result = face_list[0]
                        f_quality, f_angle = quality_check(face_result)

                        print("quality: " + str(f_quality) + ", angle: " + str(f_angle))
                        if f_quality:
                            if angle[f_angle] < 1:
                                if face.face_register(group_id='lab', user_id=username):
                                    angle[f_angle] += 1
                                    if angle[f_angle] > 0:
                                        # 这个角度完成
                                        pass
                except:
                    traceback.print_exc()
                time.sleep(0.5)
        print('Success ' + str(username) + ' register...')
        if db_flag:
            db.execute("insert into user_t (userName, realName, createTime) "
                       "values (%s, %s, now())", (username, realname))


def quality_check(face_result):
    """
    注册人脸质量控制
    Returns:

    """
    if face_result['quality']['illumination'] > 40 and \
       face_result['quality']['blur'] < 0.7 and \
       face_result['quality']['completeness'] == 1 and \
       face_result['quality']['occlusion']['left_eye'] < 0.6 and \
       face_result['quality']['occlusion']['right_eye'] < 0.6 and \
       face_result['quality']['occlusion']['nose'] < 0.7 and \
       face_result['quality']['occlusion']['mouth'] < 0.7 and \
       face_result['quality']['occlusion']['left_cheek'] < 0.8 and \
       face_result['quality']['occlusion']['right_cheek'] < 0.8 and \
       face_result['quality']['occlusion']['chin_contour'] < 0.6 and \
       abs(face_result['angle']['roll']) <= 20:
        if abs(face_result['angle']['pitch']) <= 12 and abs(face_result['angle']['yaw']) <= 12:
            return True, 0
        if -40 < face_result['angle']['pitch'] < -12 and abs(face_result['angle']['yaw']) <= 12:
            return True, 1
        if 12 < face_result['angle']['pitch'] < 40 and abs(face_result['angle']['yaw']) <= 12:
            return True, 2
        if abs(face_result['angle']['pitch']) <= 12 and -40 < face_result['angle']['yaw'] < -12:
            return True, 3
        if abs(face_result['angle']['pitch']) <= 12 and 12 < face_result['angle']['yaw'] < 40:
            return True, 4
    return False, -1


def main():
    """
    main函数 两个线程
    Returns:

    """
    t_read = threading.Thread(target=frame_read)
    t_read.start()

    t_check = threading.Thread(target=frame_register)
    t_check.start()

if __name__ == '__main__':
    main()