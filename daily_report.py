# coding=utf-8
# __author__ = 'xhm'

import db_helper
import datetime
import logging
import time


def get_name_list(db):
    name_list = db.fetchall(""" select userName, realName
                                 from user_t
                             """)
    return name_list


def main():
    """
    更新每日汇总结果到数据库
    :return:
    """
    db = db_helper.DBHelper()
    db_flag = db.connect_database()
    if db_flag:
        name_list = get_name_list(db)
        date = datetime.date.today() - datetime.timedelta(days=1)  # 前一天
        for name in name_list:
            res = db.fetchall("""select checkInTime
                                 from check_t
                                 where checkInDate = %s
                                 and userName = %s""", (date, name[0]))
            if len(res) == 2:
                total_time = res[1][0] - res[0][0]
                db.execute(""" insert into sum_t (userName, checkInDate, totalTime, startTime, endTime)
                               values (%s, %s, %s, %s, %s) 
                           """, (name[0], date, total_time, res[0][0], res[1][0]))
            else:
                print(name[0] + " no record")

if __name__ == '__main__':
    main()
