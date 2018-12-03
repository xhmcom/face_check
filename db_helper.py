# coding=utf-8
# __author__ = 'xhm'
import pymysql
import logging
import sys
import traceback

# 加入日志
# 获取logger实例
logger = logging.getLogger("baseSpider")
# 指定输出格式
formatter = logging.Formatter('%(asctime)s%(levelname)-8s:%(message)s')
# 文件日志
file_handler = logging.FileHandler("baseSpider.log")
file_handler.setFormatter(formatter)
# 控制台日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# 为logge添加具体的日志处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.setLevel(logging.INFO)


class DBHelper:
    # 构造函数
    def __init__(self, host='192.168.0.137', user='lvlab',
                 pwd='lvlab', db='face_check'):
        self.__host = host
        self.__user = user
        self.__pwd = pwd
        self.__db = db
        self.__conn = None
        self.__cur = None

    # 连接数据库
    def connect_database(self):
        try:
            self.__conn = pymysql.connect(self.__host, self.__user,
                                          self.__pwd, self.__db, charset='utf8')
        except:
            logger.error("connectDatabase failed")
            return False
        self.__cur = self.__conn.cursor()
        return True

    # 关闭数据库
    def close(self):
        # 如果数据打开，则关闭；否则没有操作
        if self.__conn and self.__cur:
            self.__cur.close()
            self.__conn.close()
        return True

    # 执行数据库的sql语句,主要用来做插入操作
    def execute(self, sql, params=None):
        # 连接数据库
        if not self.__conn:
            self.connect_database()
        try:
            if self.__conn and self.__cur:
                # 正常逻辑，执行sql，提交操作
                self.__cur.execute(sql, params)
                self.__conn.commit()
        except:
            traceback.print_exc()
            logger.error("execute failed: " + sql)
            logger.error("params: " + str(params))
            self.close()
            return False
        return True

    # 用来查询表数据
    def fetchall(self, sql, params=None):
        if not self.__conn:
            self.connect_database()
        try:
            self.execute(sql, params)
            return self.__cur.fetchall()
        except:
            traceback.print_exc()
            logger.error("execute failed: " + sql)
            logger.error("params: " + str(params))
            self.close()
        return None
