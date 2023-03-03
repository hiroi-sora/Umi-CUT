import json
import cv2

# 配置文件路径
ConfigJsonFile = "Umi-CUT_config.json"

# 配置项
ConfigDict = {
    # 1. 手动裁剪相关
    "isManualCut": False,  # 是否手动裁剪
    "manualCutApply": [0, 0],  # 手动裁剪适用分辨率，[高,宽]
    "manualCutArea": [-1, -1, -1, -1],  # 手动裁剪区域，[上,下,左,右]
    # 2. 边缘裁剪相关
    "isBorderCut": [True, True, True, True],  # 边缘是否裁剪，[上,下,左,右]
    "medianBlur": 3,  # 中值滤波 孔径的线型尺寸，奇数。0为关闭。
    "threshold": 0,  # 二值化的阈值。
    "borderColor": 0,  # 边缘颜色，0黑1白。（TODO：任意颜色）
    # 3. 重设大小相关
    "resizeMode": 0,  # 0不重设，1按倍数缩放，2指定宽度，3指定高度
    "resizeScale": 1,
    "resizeWidth": 1920,
    "resizeHeight": 1080,
    # 保存相关
    "saveExt": 0,  # 0 png，1 jpg
    "pngCompression": 3,  # png压缩，0~9，越大越小
    "jpegQuality": 95,  # jpg质量，0~100，越大越大
    # 许可后缀
    "imageSuffix": ".jpg .jpe .jpeg .jfif .png .webp .bmp .tif .tiff"
}

# ConfigDict["isManualCut"] = True

#  需要保存的设置项
SaveItem = [
    "medianBlur",
    "threshold",
    "borderColor",
    "saveExt",
    "pngCompression",
    "jpegQuality",
    "manualCutArea"
]


class ConfigModule:

    def initValue(self, optVar):
        """初始化配置。传入并设置tk变量字典"""
        self.optVar = optVar

        def load():
            """从本地json文件读取配置"""
            try:
                with open(ConfigJsonFile, "r", encoding="utf8")as fp:
                    jsonData = json.load(fp)  # 读取json文件
                    for key in jsonData:
                        if key in ConfigDict:
                            ConfigDict[key] = jsonData[key]
            except json.JSONDecodeError:  # 反序列化json错误
                self.save()
            except FileNotFoundError:  # 无配置文件
                self.save()
        load()  # 加载配置文件
        for key in optVar:
            if key in ConfigDict:
                if isinstance(ConfigDict[key], list):  # 嵌套列表
                    for i, v in enumerate(optVar[key]):
                        v.set(ConfigDict[key][i])
                else:
                    optVar[key].set(ConfigDict[key])

    def isSaveItem(self, key):
        return key in SaveItem

    def save(self):
        """保存配置到本地json文件"""
        saveDict = {}  # 提取需要保存的项
        for key in SaveItem:
            saveDict[key] = ConfigDict[key]
        with open(ConfigJsonFile, "w", encoding="utf8")as fp:
            fp.write(json.dumps(saveDict, indent=4, ensure_ascii=False))
        # print("保存")

    def update(self, key):
        """更新某个值，从tk变量读取到配置项"""
        if isinstance(ConfigDict[key], list):  # 嵌套列表
            for i, v in enumerate(self.optVar[key]):
                ConfigDict[key][i] = v.get()
        else:
            ConfigDict[key] = self.optVar[key].get()
        # print("更新", key, ConfigDict[key])

    def get(self, key=None):
        """获取一个配置项的值"""
        if not key:
            return ConfigDict
        return ConfigDict[key]

    def set(self, key, value, index=-1):
        """设置一个配置项的值"""
        # print("设置", key, value)
        if key in self.optVar:
            if not index == -1:
                self.optVar[key][index].set(value)
            else:
                self.optVar[key].set(value)
        else:
            if not index == -1:
                ConfigDict[key][index] = value
            else:
                ConfigDict[key] = value


Config = ConfigModule()  # 设置模块 单例
