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
angle_name = ['mid', 'up', 'down', 'left', 'right']
angle = [0, 0, 0, 0, 0]

def frame_read(camera_ad=0):
    """
    摄像头启动，记录帧
    Args:
        camera_ad: 摄像头地址(由于人脸采集需要采集人查看反馈信息，人脸采集在本机上完成)

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
                    if len(frame_list) > 50:
                        frame_list = []
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
        time.sleep(0.001)
        username = raw_input('username: ')
        realname = raw_input('姓名:')
        # angle 表示人脸的角度 0到4依次表示 mid, up, down, left, right
        global angle
        angle = [0, 0, 0, 0, 0]
        print(realname + "人脸采集开始，请面对摄像头，然后头部上下左右微转保持几秒")
        while not (angle[0] > 0 and angle[1] > 0 and angle[2] > 0 and angle[3] > 0 and angle[4] > 0):
            if (angle[0] + angle[1] + angle[2] + angle[3] + angle[4]) >= 3:
                break
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

                        if f_quality:

                            print("正在采集...")
                            if angle[f_angle] < 1:
                                print(str(angle_name[f_angle]) + "角度完成采集...")
                                if face.face_register(group_id='lab', user_id=username):
                                    angle[f_angle] += 1
                        else:
                            print("正在采集...")
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
        if abs(face_result['angle']['pitch']) <= 8 and abs(face_result['angle']['yaw']) <= 8 and angle[0] == 0:
            return True, 0
        elif -40 < face_result['angle']['pitch'] < -8 and angle[1] == 0:
            return True, 1
        elif 8 < face_result['angle']['pitch'] < 40 and angle[2] == 0:
            return True, 2
        elif -40 < face_result['angle']['yaw'] < -8 and angle[3] == 0:
            return True, 3
        elif 8 < face_result['angle']['yaw'] < 40 and angle[4] == 0:
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
