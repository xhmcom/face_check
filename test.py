# coding=utf-8
# __author__ = 'xhm'
import datetime
import db_helper
import cv2
import threading


# a = datetime.datetime.now()
# db = db_helper.DBHelper()
# db.execute("insert into user_t (userName, realName, createTime) "
#            "values (%s, %s, %s)", ('xuhuanmin', '徐焕旻', a))

ezopen = "ezopen://open.ys7.com/C69004173/1.hd.live"
rtmp = "rtmp://rtmp.open.ys7.com/openlive/f6a7eb05c5b645acb7821020bcf9b057.hd"
cap = cv2.VideoCapture(rtmp)


try:
    while True:
        ret, frame = cap.read()
        print(ret)
        if ret:
            cv2.imshow('Video', frame)
        c = cv2.waitKey(1)
        if c == 27:
            break
finally:
    cap.release()
    cv2.destroyAllWindows()

