from config import Config

import cv2
import numpy as np
from PIL import Image


class imgProssing:

    def __init__(self):
        self.img = {
            "raw": None,  # 0. 原始图像
            "manualCut": None,  # 1. 手动裁剪
            # "binary": None,  # 2.2. 二值化
            # "borderCut": None,  # 2. 边缘裁剪
            "output": None,  # 2. 输出
        }
        self.border = None

    def work(self, path):
        # 0. 载入图片
        img = cv2.imdecode(np.fromfile(
            path, dtype=np.uint8), cv2.IMREAD_COLOR)  # 忽略alpha通道
        self.img["raw"] = img  # 存为类变量，实际处理还是用临时变量以加快速度
        # 1. 手动裁剪
        if Config.get("isManualCut"):  # 需要手动裁剪
            manualCutApply, shape = Config.get("manualCutApply"), img.shape
            if shape[0] == manualCutApply[1] and shape[1] == manualCutApply[0]:  # 符合适用分辨率
                area = Config.get("manualCutArea")
                img = img[area[0]:area[1], area[2]:area[3]]
                print(f'长度！！！！{len(img)}')
                if len(img) == 0:
                    self.img["output"] = None
                    self.border = area
                    return
        self.img["manualCut"] = img

        # 2. 裁剪边缘
        self.border = None
        isCB = Config.get("isBorderCut")
        if not all(i is False for i in isCB):
            # 2.1. 中值滤波，消除噪点
            mbSize = Config.get("medianBlur")
            if mbSize > 0:
                img = cv2.medianBlur(img, mbSize)
            # 2.2. 二值化
            threshold = Config.get("threshold")
            if threshold > 255:
                threshold = 255
                Config.set("threshold", 255)
            elif threshold < 0:
                threshold = 0
                Config.set("threshold", 0)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 改为单通道
            # 二值化
            bColor = Config.get("borderColor")
            if bColor == 0:  # 黑
                img = cv2.threshold(
                    img, threshold, 255, cv2.THRESH_BINARY)[1]
            elif bColor == 1:  # 白
                img = cv2.threshold(
                    img, 255-threshold, 255, cv2.THRESH_BINARY_INV)[1]
            # self.img["binary"] = img
            # 2.3. 获取边缘位置 上下左右
            borderY, borderX = np.where(img == 255)
            if len(borderY) == 0 or len(borderX) == 0:
                border = (0, 0, 0, 0)  # 参数错误，给个0值
            else:
                shape = img.shape
                border = (np.min(borderY) if isCB[0] else 0,
                          np.max(borderY) if isCB[1] else shape[0],
                          np.min(borderX) if isCB[2] else 0,
                          np.max(borderX) if isCB[3] else shape[1])
            self.border = border
            # 2.4. 裁剪
            img = self.img["manualCut"][border[0]:border[1], border[2]:border[3]]
            # self.img["borderCut"] = img

        # 3. 重设大小
        resizeMode = Config.get("resizeMode")
        if not resizeMode == 0:
            shape = img.shape
            if resizeMode == 1:  # 按倍数缩放
                s = Config.get("resizeScale")
            elif resizeMode == 2:  # 按 w 缩放
                s = Config.get("resizeWidth") / shape[1]
            elif resizeMode == 2:  # 按 h 缩放
                s = Config.get("resizeWidth") / shape[0]
            img = cv2.resize(img, None, fx=s, fy=s)

        self.img["output"] = img

    def save(self, path, name):
        if self.img["output"] is None:
            return
        if Config.get("saveExt") == 0:  # png
            ext = ".png"
            params = [cv2.IMWRITE_PNG_COMPRESSION,
                      Config.get("pngCompression")]
        else:  # jpg
            ext = ".jpg"
            params = [cv2.IMWRITE_JPEG_QUALITY, Config.get("jpegQuality")]
        p = f"{path}\\{name}{ext}"  # 路径，名称，后缀
        cv2.imencode(ext, self.img["output"], params)[1].tofile(p)
        # self.show(img)

    def show(self, img=None, mode="system", winName="image"):
        """mode为opencv（使用opencv浏览器）或system（使用系统浏览器）"""
        if img is None:
            if self.img["output"] is None:
                return
            img = self.img["output"]
        if mode == "opencv":
            sp = img.shape
            scale = 720 / sp[1]
            cv2.namedWindow(winName, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(winName, int(sp[1]*scale), int(sp[0]*scale))
            cv2.imshow(winName, img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        elif mode == "system":
            imgPIL = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            imgPIL.show()


Prossing = imgProssing()

TestPath = r"D:\MyCode\PythonCode\Umi-CUT\测试 IMG_0430.PNG"
TestPath2 = r"D:\MyCode\PythonCode\Umi-CUT"
if __name__ == "__main__":
    Prossing.work(r"D:\test1.png")
    # Prossing.save(TestPath2, "测试图像")
    pass

# t2 = timeit.timeit('Prossing.work(TestPath)',
#                    'from __main__ import Prossing,TestPath', number=10)
# print(t2)


# import timeit
# t2 = timeit.timeit('cv_imread2(TestPath)',
#                    'from __main__ import cv_imread2,TestPath', number=100)


# 手动裁剪，边缘裁剪，重设大小，编码输出
