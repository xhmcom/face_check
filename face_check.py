# coding=utf-8
# __author__ = 'xhm'

from aip import AipFace
import cv2
import base64
import logging


class FaceHandler(object):
    __app_id = '14620211'
    __api_key = 'De4qbgYbcvusHHquWBfsrt5k'
    __secret_key = 'nGZ1nnH2GQL1gY54XlXlc52HekdH7xm3'

    def __init__(self, group_id='lab'):
        """
        构造函数
        Args:
            group_id:
        """
        self.__client = AipFace(self.__app_id, self.__api_key, self.__secret_key)
        self.__client.setConnectionTimeoutInMillis(2000)
        self.__client.setSocketTimeoutInMillis(2000)
        # init
        self.image = ''
        self.image_type = ''
        self.group_id = group_id
        self.face_dict = dict()
        self.reg_dict = dict()

    @staticmethod
    def __error_warning(result_dict):
        """
        sdk接口error提示
        Args:
            result_dict:

        Returns:

        """
        if result_dict['error_code'] == 0:
            return True
        else:
            logging.warning(" Error: " + "Error_code: " + str(result_dict['error_code'])
                                       + " Error_msg: " + str(result_dict['error_msg']))
            return False

    def set_image(self, image, image_type):
        """
        设置待检测image
        Args:
            image:
            image_type:

        Returns:

        """
        assert image_type == 'BASE64' or image_type == 'URL' or image_type == 'FACE_TOKEN', 'image input type error'
        self.image = image
        self.image_type = image_type

    def get_faces(self):
        """
        获取人脸检测中检测到的人脸列表
        Returns:

        """
        if not self.face_dict:
            return None
        if self.__error_warning(self.face_dict) and self.face_dict['result']['face_num'] > 0:
            return self.face_dict['result']['face_list']
        return None

    def face_detect(self):
        """
        人脸检测，将人脸临时token记录
        Returns:
            是否有人脸
        """
        options = dict()
        options["max_face_num"] = 1
        options["face_field"] = 'quality'
        self.face_dict = self.__client.detect(self.image, self.image_type, options)
        #print(self.face_dict) # test
        if self.__error_warning(self.face_dict) and self.face_dict['result']['face_num'] > 0:
            self.image = self.face_dict['result']['face_list'][0]['face_token']
            self.image_type = 'FACE_TOKEN'
            return True
        else:
            return False

    def face_search(self):
        """
        人脸搜索（包含质量检测）
        Returns:

        """
        options = dict()
        options["quality_control"] = "NONE"
        options["liveness_control"] = "NONE"
        options["max_user_num"] = 1
        user_dict = self.__client.search(self.image, self.image_type, self.group_id, options)
        print(user_dict) # test
        try:
            user_time = user_dict['timestamp']
        except:
            print('notimestamp')
            return 0, 'unknown'
        if self.__error_warning(user_dict):
            max_pro_user = user_dict['result']['user_list'][0]
            print(max_pro_user['score'])
            if max_pro_user['score'] >= 85:
                return user_time, max_pro_user['user_id']

        return user_time, 'unknown'

    def face_register(self, group_id, user_id, reg_image=None, reg_image_type=None):
        """
        人脸注册
        Returns:
            注册是否成功
        """
        if reg_image is None:
            reg_image = self.image
        if reg_image_type is None:
            reg_image_type = self.image_type
        self.reg_dict = self.__client.addUser(reg_image, reg_image_type, group_id, user_id)
        if self.__error_warning(self.reg_dict):
            return True
        else:
            return False


def get_base64(img):
    """
        cv2图像转base64
    Args:
        img: cv2 图像

    Returns:

    """
    height, width = img.shape[:2]
    while height > 256 and width > 256:
        height //= 2
        width //= 2
    img_np = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    tmp = cv2.imencode('.jpg', img_np)[1]
    img_base64 = str(base64.b64encode(tmp))
    return img_base64


def test(image_path='d:\\Users\\Xuuu\\Pictures\\dd.jpg'):
    face = FaceHandler()
    img = cv2.imread(image_path)
    # opencv to base64
    image_base64 = get_base64(img)
    face.set_image(image_base64, 'BASE64')

    if face.face_detect():
        face_time, person = face.face_search()
        print(face_time)
        print(person)

if __name__ == '__main__':
    test()

