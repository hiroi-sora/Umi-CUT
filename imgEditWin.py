from config import Config
from processingAPI import Prossing
from asset import IconPngBase64  # 资源

import os
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from windnd import hook_dropfiles  # 文件拖拽
from PIL import Image, ImageTk


class imgEditWin:
    def __init__(self, toClose=None, defaultPath=""):
        self.toClose = toClose

        def initWin():  # 初始化窗口
            self.win = tk.Toplevel()
            # self.win = tk.Tk()
            self.win.protocol("WM_DELETE_WINDOW", self.onClose)
            self.win.title("参数配置")
            self.win.resizable(False, False)  # 禁止窗口拉伸
            # 图标
            self.iconImg = tkinter.PhotoImage(
                data=IconPngBase64)  # 载入图标，base64转
            self.win.iconphoto(False, self.iconImg)  # 设置窗口图标
        initWin()

        def initVar():  # 初始化变量
            self.imgResize = (-1, -1)  # 展示图像尺寸
            self.imgSize = (-1, -1)  # 图像真实尺寸
            self.imgFile = None
            self.imgScale = -1
            self.imgPath = ""
            self.mainCanvasImg = None
            self.isLoading = False  # 是否加载中
            self.mcLines = []  # 手动裁剪线
            self.cfgVar = {  # 设置项tk变量
                # 1. 手动裁剪相关
                "isManualCut": tk.BooleanVar(),  # 是否手动裁剪
                "manualCutArea": [  # 手动裁剪区域，[上,下,左,右]
                    tk.IntVar(), tk.IntVar(), tk.IntVar(), tk.IntVar(),
                ],
                # 2. 边缘裁剪相关
                "isBorderCut": [  # 边缘是否裁剪，[上,下,左,右]
                    tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(),
                ],
                "borderColor": tk.IntVar(),  # 边缘颜色，0黑1白。
                "medianBlur": tk.IntVar(),  # 中值滤波 孔径的线型尺寸，奇数。0为关闭。
                "threshold": tk.IntVar(),  # 二值化的阈值。
                # 3. 重设大小相关
                "resizeMode": tk.IntVar(),  # 0不重设，1按倍数缩放，2指定宽度，3指定高度
                "resizeScale": tk.DoubleVar(),
                "resizeWidth": tk.IntVar(),
                "resizeHeight": tk.IntVar(),
                # 保存相关
                "saveExt": tk.IntVar(),  # 0 png，1 jpg
                "pngCompression": tk.IntVar(),  # png压缩，0~9，越大越小
                "jpegQuality": tk.IntVar(),  # jpg质量，0~100，越大越大
            }
            Config.initValue(self.cfgVar)  # 初始化设置项

            # 面板值改变时，更新到配置值，并写入本地
            self.saveTimer = None  # 计时器，改变面板值一段时间后写入本地
            self.drawTimer = None

            def configSave():  # 保存值的事件
                Config.save()
                self.saveTimer = None

            def reDrawFun():
                self.loadImage(self.imgPath)
                self.drawTimer = None

            def valueChange(key):  # 值改变的事件
                Config.update(key)  # 更新配置项
                if Config.isSaveItem(key):
                    if self.saveTimer:  # 计时器已存在，则停止已存在的
                        self.win.after_cancel(self.saveTimer)
                        self.saveTimer = None
                    self.saveTimer = self.win.after(200, configSave)
                reDraw = ["isManualCut", "manualCutArea",  # 改变后需要重绘的项目
                          "isBorderCut", "medianBlur", "threshold", "borderColor"]
                if not self.isLoading and key in reDraw:  # 非加载中才能用
                    if self.drawTimer:  # 计时器已存在，则停止已存在的
                        self.win.after_cancel(self.drawTimer)
                        self.drawTimer = None
                    self.drawTimer = self.win.after(200, reDrawFun)
            for key in self.cfgVar:  # 跟踪值改变事件
                if isinstance(self.cfgVar[key], list):  # 嵌套列表
                    for i in self.cfgVar[key]:
                        i.trace("w", lambda *e, key=key: valueChange(key))
                else:
                    self.cfgVar[key].trace(
                        "w", lambda *e, key=key: valueChange(key))
        initVar()

        def initCtrl():  # 初始化控制中心
            # tk.Frame(self.win, height=10).pack(side='top')
            ctrlFrame = tk.Frame(self.win)
            ctrlFrame.pack(side='top')

            def initInputImg():  # 初始化输入图片展示
                width = 120
                fr = tk.LabelFrame(ctrlFrame, text="预览图片", width=width+10)
                fr.pack(side='left', ipadx=5, ipady=5,
                        fill="y", pady=5, padx=5)
                fr.pack_propagate(False)
                tk.Button(fr, text='打开图片', width=15,
                          command=self.loadImage).pack()
                tk.Label(fr).pack()
                self.textImgSize = tk.StringVar()
                self.textImgPath = tk.StringVar()
                tk.Label(fr, wraplength=width, justify='left', anchor='w',
                         textvariable=self.textImgSize).pack(fill="x")
                tk.Label(fr, wraplength=width, justify='left', anchor='w',
                         textvariable=self.textImgPath).pack(fill="x")
            initInputImg()

            def initManualCut():  # 初始化手动裁剪设置
                fr = tk.LabelFrame(ctrlFrame, text="手动裁剪")
                fr.pack(side='left', ipadx=5, ipady=5,
                        fill="y", pady=5, padx=5)
                tk.Checkbutton(fr, text="启用", variable=self.cfgVar["isManualCut"]).grid(
                    column=0, row=0, columnspan=2, sticky="w")
                btn = tk.Label(fr, text="重置", fg="blue", cursor="hand2")
                btn.grid(column=3, row=0, columnspan=2, sticky="w")
                btn.bind('<Button-1>', self.reManualCut)
                tk.Label(fr, text="上:").grid(column=0, row=2, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["manualCutArea"][0]).grid(
                    column=1, row=2, sticky="w")
                tk.Label(fr, text="下:").grid(column=3, row=2, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["manualCutArea"][1]).grid(
                    column=4, row=2, sticky="w")
                tk.Label(fr, text="左:").grid(column=0, row=4, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["manualCutArea"][2]).grid(
                    column=1, row=4, sticky="w")
                tk.Label(fr, text="右:").grid(column=3, row=4, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["manualCutArea"][3]).grid(
                    column=4, row=4, sticky="w")
                tk.Label(fr, text="适用分辨率：", fg="gray").grid(
                    column=0, row=5, columnspan=5, sticky="w")
                tk.Label(fr, textvariable=self.textImgSize, fg="gray").grid(
                    column=0, row=6, columnspan=5, sticky="w")
                tk.Label(fr, text="↓ 红色框为手动裁剪框", fg="gray").grid(
                    column=0, row=7, columnspan=5, sticky="w")
                fr.grid_columnconfigure(2, minsize=10)
                fr.grid_rowconfigure(3, minsize=5)
            initManualCut()

            def initBorderCut():  # 初始化边缘裁剪设置
                fr = tk.LabelFrame(ctrlFrame, text="自动裁剪黑边")
                fr.pack(side='left', ipadx=5, ipady=5, fill="y", pady=5)

                def setBorder(e):
                    for i in self.cfgVar["isBorderCut"]:
                        i.set(e)
                btn1 = tk.Label(fr, text="全部启用", fg="blue", cursor="hand2")
                btn1.grid(column=0, row=0, columnspan=2, sticky="w")
                btn1.bind('<Button-1>', lambda *e: setBorder(True))
                btn2 = tk.Label(fr, text="全部禁用", fg="red", cursor="hand2")
                btn2.grid(column=2, row=0, columnspan=2, sticky="w")
                btn2.bind('<Button-1>', lambda *e: setBorder(False))
                tk.Checkbutton(fr, text="上", variable=self.cfgVar["isBorderCut"][0]).grid(
                    column=0, row=1, sticky="w")
                tk.Checkbutton(fr, text="下", variable=self.cfgVar["isBorderCut"][1]).grid(
                    column=1, row=1, sticky="w")
                tk.Checkbutton(fr, text="左", variable=self.cfgVar["isBorderCut"][2]).grid(
                    column=2, row=1, sticky="w")
                tk.Checkbutton(fr, text="右", variable=self.cfgVar["isBorderCut"][3]).grid(
                    column=3, row=1, sticky="w")
                tk.Label(fr, text="边缘颜色:").grid(
                    column=0, row=2, columnspan=2, sticky="w")
                tk.Radiobutton(
                    fr, text='黑', variable=self.cfgVar["borderColor"], value=0).grid(
                    column=2, row=2, sticky="w")
                tk.Radiobutton(
                    fr, text='白', variable=self.cfgVar["borderColor"], value=1).grid(
                    column=3, row=2, sticky="w")
                tk.Label(fr, text="中值滤波( >0奇数 ):").grid(
                    column=0, row=3, columnspan=3, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["medianBlur"]).grid(
                    column=3, row=3, sticky="w")
                tk.Label(fr, text="阈值( 0~255 ):").grid(
                    column=0, row=5, columnspan=3, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["threshold"]).grid(
                    column=3, row=5, sticky="w")
                tk.Label(fr, text="↓ 虚线框为去黑边裁剪框(最终输出)", fg="gray").grid(
                    column=0, row=10, columnspan=10, sticky="w")
            initBorderCut()

            def initResize():  # 初始化重设大小设置
                fr = tk.LabelFrame(ctrlFrame, text="重设图片大小")
                fr.pack(side='left', ipadx=5, ipady=5,
                        fill="y", pady=5, padx=5)
                tk.Radiobutton(fr, text='保持原本', value=0, variable=self.cfgVar["resizeMode"]
                               ).grid(column=0, row=0, sticky="w")
                tk.Radiobutton(fr, text='指定倍数', value=1, variable=self.cfgVar["resizeMode"]
                               ).grid(column=0, row=1, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["resizeScale"]).grid(
                    column=1, row=1, sticky="w")
                tk.Label(fr, text="倍").grid(column=2, row=1, sticky="w")
                tk.Radiobutton(fr, text='宽度不大于', value=2, variable=self.cfgVar["resizeMode"]
                               ).grid(column=0, row=2, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["resizeWidth"]).grid(
                    column=1, row=2, sticky="w")
                tk.Label(fr, text="像素").grid(column=2, row=2, sticky="w")
                tk.Radiobutton(fr, text='高度不大于', value=3, variable=self.cfgVar["resizeMode"]
                               ).grid(column=0, row=3, sticky="w")
                tk.Entry(fr, width=5, textvariable=self.cfgVar["resizeHeight"]).grid(
                    column=1, row=3, sticky="w")
                tk.Label(fr, text="像素").grid(column=2, row=3, sticky="w")
                tk.Label(fr, text="比例均保持不变。", fg="gray").grid(
                    column=0, row=4, sticky="w", columnspan=5)
            initResize()

            def initOutput():  # 初始化输出文件设置
                fr = tk.LabelFrame(ctrlFrame, text="压缩图片体积")
                fr.pack(side='left', ipadx=5, ipady=5, fill="y", pady=5)
                tk.Radiobutton(fr, text='保存为 png 格式', value=0, variable=self.cfgVar["saveExt"]
                               ).grid(column=0, row=0, columnspan=5, sticky="w")
                tk.Label(fr, text="压缩率").grid(column=0, row=1, sticky="w")
                tk.Entry(fr, width=4, textvariable=self.cfgVar["pngCompression"]).grid(
                    column=1, row=1, sticky="w")
                tk.Label(fr, text="0-9，数值越大体积越小", fg="gray"
                         ).grid(column=0, row=2, columnspan=5, sticky="w")

                tk.Radiobutton(fr, text='保存为 jpg 格式', value=1, variable=self.cfgVar["saveExt"]
                               ).grid(column=0, row=4, columnspan=5, sticky="w")
                tk.Label(fr, text="质量").grid(column=0, row=5, sticky="w")
                tk.Entry(fr, width=4, textvariable=self.cfgVar["jpegQuality"]).grid(
                    column=1, row=5, sticky="w")
                tk.Label(fr, text="0-100，数值越小体积越小", fg="gray"
                         ).grid(column=0, row=6, columnspan=5, sticky="w")
            initOutput()

            def initBtn():
                fr = tk.LabelFrame(ctrlFrame, text="调整好了")
                fr.pack(side='left', padx=5, ipady=10, fill="y", pady=5)
                tk.Button(fr, text='完  成', command=self.onClose, bg="pale turquoise",
                          width=10, height=3).pack(padx=5)
                tk.Button(fr, text='预  览', command=Prossing.show, bg="khaki1",
                          width=10, height=2,).pack(side="bottom", padx=5, pady=10)
            initBtn()
        initCtrl()

        def initCanvas():  # 初始化画板
            self.cW = 960  # 画板尺寸
            self.cH = 540
            self.mainCanvas = tk.Canvas(self.win, width=self.cW, height=self.cH,
                                        bg="gray", borderwidth=0)
            self.mainCanvas.pack()
        initCanvas()

        # self.draw()
        hook_dropfiles(self.win, func=self.draggedFiles)  # 注册文件拖入
        if defaultPath:  # 打开默认图片
            self.loadImage(defaultPath)
        self.win.mainloop()

    def draggedFiles(self, paths):  # 拖入文件
        self.loadImage(paths[0].decode("gbk"))

    def loadImage(self, path=None):  # 载入新图片
        if not path:
            suf = Config.get("imageSuffix")  # 许可后缀
            path = tk.filedialog.askopenfilename(
                title='选择预览图片', filetypes=[("图片", suf)])
            self.win.lift()  # 窗口提到最前
            if not path:
                return
        try:
            img = Image.open(path)
        except Exception as e:
            tk.messagebox.showwarning(
                "遇到了一点小问题", f"图片载入失败。图片地址：\n{path}\n\n错误信息：\n{e}")
            return
        self.isLoading = True
        medianBlur = Config.get("medianBlur")
        if medianBlur < 0:
            medianBlur = 0
        if not medianBlur == 0 and medianBlur % 2 == 0:
            medianBlur += 1
        Config.set("medianBlur", medianBlur)
        Config.set("manualCutApply", img.size)
        self.imgPath = path
        self.imgSize = img.size
        self.textImgSize.set(f"{img.size[0]} x {img.size[1]}")
        self.textImgPath.set(f"路径：{path}")
        # 检测图片大小
        sw, sh = self.cW/img.size[0], self.cH/img.size[1]
        if sw > sh:  # 测试，按宽、还是高缩放，刚好填满画布
            resize = (round(img.size[0]*sh), self.cH)
        else:
            resize = (self.cW, round(img.size[1]*sw))
        self.imgScale = resize[0]/img.size[0]  # 记录缩放系数，原分辨率*系数=绘制分辨率
        if not self.imgResize == resize:  # 跟之前不同
            self.imgResize = resize
        # 绘制
        self.mainCanvas.delete(tk.ALL)  # 清除画板
        self.drawManualCut()  # 手动裁剪
        self.drawBorderCut(path)  # 边缘裁剪
        # 缓存图片并显示
        img = img.resize(resize, Image.ANTIALIAS)  # 改变图片大小
        self.imgFile = ImageTk.PhotoImage(img)  # 缓存图片
        self.mainCanvasImg = self.mainCanvas.create_image(
            0, 0, anchor='nw', image=self.imgFile)  # 绘制图片
        self.mainCanvas.tag_lower(self.mainCanvasImg)  # 该元素移动到最下方，防止挡住矩形们
        self.isLoading = False

    def drawManualCut(self):  # 绘制手动裁剪
        if Config.get("isManualCut"):
            # 获取并重设数值
            area = Config.get("manualCutArea")
            if all(i < 0 for i in area):  # 任意-1存在，重置
                self.reManualCut()
                area = Config.get("manualCutArea")[:]  # 重新深拷贝
            else:
                area = Config.get("manualCutArea")[:]
                # 防止出界
                for i in (0, 1, 2, 3):
                    if area[i] < 0:
                        area[i] = 0
                    wh = 1 if i in (0, 1) else 0
                    if area[i] > self.imgSize[wh]:
                        area[i] = self.imgSize[wh]
                # 防止相反
                if area[0] > area[1]:
                    area[1] = area[0]
                if area[2] > area[3]:
                    area[3] = area[2]
                for i in range(4):  # 设回
                    Config.set("manualCutArea", area[i], i)
            # 计算画板映射值
            for i in range(4):
                area[i] = area[i] * self.imgScale  # 转为映射值
            lineXY = [
                #  p1x      p1y      p2x     p2y
                [area[2], area[0], area[3], area[0]],  # 上
                [area[2], area[1], area[3], area[1]],  # 下
                [area[2], area[0], area[2], area[1]],  # 左
                [area[3], area[0], area[3], area[1]],  # 右
            ]
            for i in range(4):
                for ii in range(4):
                    lineXY[i][ii] += 3
                l = self.mainCanvas.create_line(  # 绘制实线
                    lineXY[i][0], lineXY[i][1], lineXY[i][2], lineXY[i][3], fill='red', width=6)
                self.mcLines.append(l)
        else:  # 关闭裁剪
            for i in range(len(self.mcLines)):
                l = self.mcLines.pop()
                self.mainCanvas.delete(l)

    def reManualCut(self, e=None):  # 重置手动裁剪
        if Config.get("isManualCut"):
            flag = self.isLoading
            self.isLoading = True
            area = [0,  # 上
                    self.imgSize[1],  # 下
                    0,  # 左
                    self.imgSize[0],  # 右
                    ]
            for i in range(3):  # 设回
                Config.set("manualCutArea", area[i], i)
            self.isLoading = flag
            Config.set("manualCutArea", area[3], 3)

    def drawBorderCut(self, path):  # 绘制边缘裁剪
        Prossing.work(path)
        border = Prossing.border
        if border:
            p1x = round(border[2] * self.imgScale)
            p1y = round(border[0] * self.imgScale)
            if p1x < 3:
                p1x = 3
            if p1y < 3:
                p1y = 3
            p2x = round(border[3] * self.imgScale)
            p2y = round(border[1] * self.imgScale)
            if Config.get("isManualCut"):  # 加上手动裁剪
                manualCutArea = Config.get("manualCutArea")
                xp = manualCutArea[2]*self.imgScale
                yp = manualCutArea[0]*self.imgScale
                p1x += xp
                p2x += xp
                p1y += yp
                p2y += yp
            r1 = self.mainCanvas.create_rectangle(
                p1x, p1y, p2x, p2y, outline='white', width=2)  # 绘制白实线基底
            r2 = self.mainCanvas.create_rectangle(
                p1x, p1y, p2x, p2y, outline='black', width=2, dash=4)  # 绘制黑虚线表层
            self.mainCanvas.tag_lower(r2)  # 移动到最下方
            self.mainCanvas.tag_lower(r1)

    def onClose(self):
        if self.toClose:
            self.toClose()
        self.win.destroy()  # 销毁窗口


# 测试
if __name__ == "__main__":
    # imgEditWin(defaultPath=r"D:\MyCode\PythonCode\Umi-CUT\测试 IMG_0430.PNG")
    imgEditWin()
