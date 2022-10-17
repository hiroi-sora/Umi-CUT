from imgEditWin import imgEditWin  # 子窗口
from asset import IconPngBase64, GetHelpText  # 资源
from processingAPI import Prossing  # opencv
from config import Config

import os
import time
import asyncio  # 异步
import threading  # 线程
from PIL import Image
import tkinter as tk
import tkinter.filedialog
from tkinter import Variable, ttk
from windnd import hook_dropfiles  # 文件拖拽
from webbrowser import open as webOpen  # “关于”面板打开项目网址

ProjectVer = "1.0.2"  # 版本号
ProjectName = f"Umi-CUT 图片裁剪/去黑边 v{ProjectVer}"  # 名称
ProjectWeb = "https://github.com/hiroi-sora/Umi-CUT"


class Win:
    def __init__(self):
        self.imgDict = {}  # 当前载入的图片信息字典，key为表格组件id。必须为有序字典，python3.6以上默认是。
        self.isRunning = 0  # 0未在运行，1正在运行，2正在停止

        # 1.初始化主窗口
        def initWin():
            self.win = tk.Tk()
            self.win.title(ProjectName)
            # 窗口大小与位置
            w, h = 360, 500  # 窗口初始大小与最小大小
            ws, hs = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
            x, y = round(ws/2 - w/2), round(hs/2 - h/2)  # 初始位置，屏幕正中
            self.win.minsize(w, h)  # 最小大小
            self.win.geometry(f"{w}x{h}+{x}+{y}")  # 初始大小与位置
            self.win.protocol("WM_DELETE_WINDOW", self.onClose)  # 窗口关闭
            # 图标
            self.iconImg = tkinter.PhotoImage(
                data=IconPngBase64)  # 载入图标，base64转
            self.win.iconphoto(False, self.iconImg)  # 设置窗口图标
        initWin()

        # 2.初始化变量
        def initVar():
            self.strManualCut = tk.StringVar()
            self.strBorderCut = tk.StringVar(value="123")
            self.strResize = tk.StringVar()
            self.strSave = tk.StringVar()
            self.strOutFolder = tk.StringVar(value="# 裁剪")
        initVar()

        # 3. 初始化组件
        def initTop():  # 顶部按钮
            tk.Frame(self.win, height=5).pack(side='top')
            fr = tk.Frame(self.win)
            fr.pack(side='top', fill="x", padx=5)
            # 右侧按钮
            self.btnRun = tk.Button(
                fr, text='开始任务', width=12, height=2,  command=self.run)
            self.btnRun.pack(side='right', padx=5)
            # 左侧文本和进度条
            vFrame2 = tk.Frame(fr)
            vFrame2.pack(side='top', fill='x')
            self.labelPercentage = tk.Label(vFrame2, text="0%")  # 进度百分比 99%
            self.labelPercentage.pack(side='right', padx=2)
            self.labelFractions = tk.Label(vFrame2, text="0/0")  # 进度分数 99/100
            self.labelFractions.pack(side='right')
            self.labelTime = tk.Label(vFrame2, text="0s")  # 已用时间 12.3s
            self.labelTime.pack(side='right', padx=5)
            self.progressbar = ttk.Progressbar(fr)
            self.progressbar.pack(side='top', padx=5, fill="x")
        initTop()

        self.notebook = ttk.Notebook(self.win)  # 初始化选项卡组件
        self.notebook.pack(expand=True, fill=tk.BOTH)  # 填满父组件

        def initTab1():  # 表格卡
            tabFrame = tk.Frame(self.notebook)  # 选项卡主容器
            self.notebook.add(tabFrame, text=f'{"处理列表": ^10s}')
            # 顶栏
            fr1 = tk.Frame(tabFrame)
            fr1.pack(side='top', fill='x', pady=2)
            tk.Button(fr1, text=' 浏览 ',  command=self.openFileWin).pack(
                side='left', padx=5)
            tk.Label(fr1, text="或直接拖入").pack(side='left')
            tk.Button(fr1, text='清空表格', width=12, command=self.clearTable).pack(
                side='right')
            tk.Button(fr1, text='移除选中图片', width=12, command=self.delImgList).pack(
                side='right', padx=5)
            # 表格主体
            fr2 = tk.Frame(tabFrame)
            fr2.pack(side='top', fill='both')
            self.table = ttk.Treeview(
                master=fr2,  # 父容器
                height=50,  # 表格显示的行数,height行
                columns=['name', 'time'],  # 显示的列
                show='headings',  # 隐藏首列
            )
            hook_dropfiles(self.table, func=self.draggedImages)  # 注册文件拖入
            self.table.pack(expand=True, side="left", fill='both')
            self.table.heading('name', text='文件名称')
            self.table.heading('time', text='耗时')
            self.table.column('name', minwidth=40)
            self.table.column('time', width=20, minwidth=20)
            vbar = tk.Scrollbar(  # 绑定滚动条
                fr2, orient='vertical', command=self.table.yview)
            vbar.pack(side="left", fill='y')
            self.table["yscrollcommand"] = vbar.set
        initTab1()

        def initTab3():  # 设置卡
            tabFrame = tk.Frame(self.notebook)  # 选项卡主容器
            self.notebook.add(tabFrame, text=f'{"设置": ^10s}')

            def initOptFrame():  # 初始化可滚动画布 及 内嵌框架
                optVbar = tk.Scrollbar(
                    tabFrame, orient="vertical")  # 创建滚动条
                optVbar.pack(side="right", fill="y")
                self.optCanvas = tk.Canvas(
                    tabFrame, highlightthickness=0)  # 创建画布，用于承载框架。highlightthickness取消高亮边框
                self.optCanvas.pack(side="left", fill="both",
                                    expand="yes")  # 填满父窗口
                self.optCanvas["yscrollcommand"] = optVbar.set  # 绑定滚动条
                optVbar["command"] = self.optCanvas.yview
                self.optFrame = tk.Frame(self.optCanvas)  # 容纳设置项的框架
                self.optFrame.pack()
                self.optCanvas.create_window(  # 框架塞进画布
                    (0, 0), window=self.optFrame, anchor="nw")
            initOptFrame()

            LabelFramePadY = 3  # 每个区域上下间距

            def initOutpot():
                fr1 = tk.LabelFrame(self.optFrame, text="输出文件")
                fr1.pack(side='top', fill='x', ipady=2,
                         pady=LabelFramePadY, padx=4)
                fr = tk.Frame(fr1)
                fr.pack(fill='x', pady=4, padx=8)
                tk.Label(fr, text="输出文件夹位于第一张图片的文件夹中", fg="gray").grid(
                    column=0, row=0, sticky="w", columnspan=2)
                tk.Label(fr, text="输出文件夹名称：").grid(column=0, row=2, sticky="w")
                tk.Entry(
                    fr, textvariable=self.strOutFolder).grid(column=1, row=2,  sticky="nsew")
            initOutpot()

            def initStrHub():
                tk.Label(self.optFrame).pack()
                tk.Button(self.optFrame, text='参 数 设 置', bg="cyan", width=30,
                          height=2,  command=self.openCtrlWin).pack()
                fr = tk.LabelFrame(self.optFrame, text="手动裁剪参数")
                fr.pack(side='top', fill='x', ipady=2,
                        pady=LabelFramePadY, padx=4)
                tk.Label(fr, textvariable=self.strManualCut, fg="gray",
                         justify='left', anchor='w').pack(fill="x")
                fr = tk.LabelFrame(
                    self.optFrame, text="自动裁剪黑边参数")
                fr.pack(side='top', fill='x', ipady=2,
                        pady=LabelFramePadY, padx=4)
                tk.Label(fr, textvariable=self.strBorderCut, fg="gray",
                         justify='left', anchor='w',).pack(fill="x")
                fr = tk.LabelFrame(
                    self.optFrame, text="重设大小参数")
                fr.pack(side='top', fill='x', ipady=2,
                        pady=LabelFramePadY, padx=4)
                tk.Label(fr, textvariable=self.strResize, fg="gray",
                         justify='left', anchor='w',).pack(fill="x")
                fr = tk.LabelFrame(
                    self.optFrame, text="输出图片参数")
                fr.pack(side='top', fill='x', ipady=2,
                        pady=LabelFramePadY, padx=4)
                tk.Label(fr, textvariable=self.strSave, fg="gray",
                         justify='left', anchor='w',).pack(fill="x")
            initStrHub()

            def initAbout():  # 关于面板
                frameAbout = tk.LabelFrame(
                    self.optFrame, text="关于")
                frameAbout.pack(side='top', fill='x', ipady=2,
                                pady=LabelFramePadY, padx=4)
                tk.Label(frameAbout, image=self.iconImg).pack()  # 图标
                tk.Label(frameAbout, text=ProjectName, fg="gray").pack()
                labelWeb = tk.Label(frameAbout, text=ProjectWeb, cursor="hand2",
                                    fg="deeppink")
                labelWeb.pack()  # 文字
                labelWeb.bind(  # 绑定鼠标左键点击，打开网页
                    '<Button-1>', self.openProjectWeb)
            initAbout()

            def initOptFrameWH():  # 初始化框架的宽高
                self.optFrame.update()  # 强制刷新
                rH = self.optFrame.winfo_height()  # 由组件撑起的 框架高度
                self.optCanvas.config(scrollregion=(0, 0, 0, rH))  # 画布内高度为框架高度
                self.optFrame.pack_propagate(False)  # 禁用框架自动宽高调整
                self.optFrame["height"] = rH  # 手动还原高度。一次性设置，之后无需再管。
                self.optCanvasWidth = 1  # 宽度则是随窗口大小而改变。

                def onCanvasResize(event):  # 绑定画布大小改变事件
                    cW = event.width-3  # 当前 画布宽度
                    if not cW == self.optCanvasWidth:  # 若与上次不同：
                        self.optFrame["width"] = cW  # 修改设置页 框架宽度
                        self.optCanvasWidth = cW
                self.optCanvas.bind(  # 绑定画布大小改变事件。只有画布组件前台显示时才会触发，减少性能占用
                    '<Configure>', onCanvasResize)

                def onCanvasMouseWheel(event):  # 绑定画布中滚轮滚动事件
                    self.optCanvas.yview_scroll(
                        1 if event.delta < 0 else -1, "units")
                self.optCanvas.bind_all("<MouseWheel>", onCanvasMouseWheel)
            initOptFrameWH()

            # self.notebook.select(tabFrame)

        initTab3()

        def initTab2():  # 使用说明
            self.tabFrameOutput = tk.Frame(self.notebook)  # 选项卡主容器
            self.notebook.add(self.tabFrameOutput, text=f'{"使用说明": ^10s}')
            fr2 = tk.Frame(self.tabFrameOutput)
            fr2.pack(side='top', fill='both')
            vbar = tk.Scrollbar(fr2, orient='vertical')  # 滚动条
            vbar.pack(side="right", fill='y')
            textOutput = tk.Text(fr2, height=500, width=500)
            textOutput.pack(fill='both', side="left")
            vbar["command"] = textOutput.yview
            textOutput["yscrollcommand"] = vbar.set
            textOutput.insert(tk.END, GetHelpText(ProjectWeb))
        initTab2()

        self.loadConfig()
        self.win.mainloop()

    # 加载图片 ===============================================

    def draggedImages(self, paths):  # 拖入图片
        if not self.isRunning == 0:
            return
        pathList = []
        for p in paths:  # byte转字符串
            pathList.append(p.decode("gbk"))
        self.addImagesList(pathList)

    def openFileWin(self):  # 打开选择文件窗
        if not self.isRunning == 0:
            return
        suf = Config.get("imageSuffix")  # 许可后缀
        paths = tk.filedialog.askopenfilenames(
            title='选择图片', filetypes=[('图片', suf)])
        self.addImagesList(paths)

    def addImagesList(self, paths):  # 添加一批图片列表
        suf = Config.get("imageSuffix").split()  # 许可后缀列表

        def addImage(path):  # 添加一张图片。传入路径，许可后缀。
            path = path.replace("/", "\\")  # 浏览是左斜杠，拖入是右斜杠；需要统一
            if suf and os.path.splitext(path)[1].lower() not in suf:
                return  # 需要判别许可后缀 且 文件后缀不在许可内，不添加。
            # 检测是否重复
            for key, value in self.imgDict.items():
                if value["path"] == path:
                    return
            # 检测是否可用
            try:
                s = Image.open(path).size
            except Exception as e:
                tk.messagebox.showwarning(
                    "遇到了一点小问题", f"图片载入失败。图片地址：\n{path}\n\n错误信息：\n{e}")
                return
            # 加入待处理列表
            name = os.path.basename(path)  # 带后缀的文件名
            tableInfo = (name, "")
            id = self.table.insert('', 'end', values=tableInfo)  # 添加到表格组件中
            dictInfo = {"name": name, "path": path, "size": s}
            self.imgDict[id] = (dictInfo)  # 添加到字典中

        for path in paths:  # 遍历拖入的所有路径
            if os.path.isdir(path):  # 若是目录
                subFiles = os.listdir(path)  # 遍历子文件
                for s in subFiles:
                    addImage(path+"\\"+s)  # 添加
            elif os.path.isfile(path):  # 若是文件：
                addImage(path)  # 直接添加

    # 参数配置 ===============================================

    def loadConfig(self):
        c = Config.get()
        if c["isManualCut"]:
            self.strManualCut.set(
                f"已启用手动裁剪\n适用分辨率：{c['manualCutApply'][0]}x{c['manualCutApply'][1]}\n\n区域：\n上：{c['manualCutArea'][0]}    下：{c['manualCutArea'][1]}\n左：{c['manualCutArea'][2]}    右：{c['manualCutArea'][3]}")
        else:
            self.strManualCut.set("未启用手动裁剪")
        if True in c["isBorderCut"]:
            s = ("上 " if c["isBorderCut"][0] else "") +\
                ("下 " if c["isBorderCut"][1] else "") +\
                ("左 " if c["isBorderCut"][2] else "") +\
                ("右 " if c["isBorderCut"][3] else "")
            bcolor = '黑色' if c['borderColor'] == 0 else '白色'
            self.strBorderCut.set(
                f"已启用自动去黑边\n方向：{s}\n\n边缘颜色：{bcolor}\n\n中值滤波孔径：{c['medianBlur']}\n\n边框深色阈值：{c['threshold']}")
        else:
            self.strBorderCut.set("未启用自动去黑边")
        if c["resizeMode"] == 0:
            self.strResize.set("不改变输出图片大小")
        elif c["resizeMode"] == 1:
            self.strResize.set(f"缩放至 {c['resizeScale']} 倍")
        elif c["resizeMode"] == 2:
            self.strResize.set(f"缩放宽度不大于 {c['resizeWidth']} 像素")
        elif c["resizeMode"] == 3:
            self.strResize.set(f"缩放高度不大于 {c['resizeHeight']} 像素")
        if c["saveExt"] == 0:
            self.strSave.set(
                f"保存为 .png\n压缩系数：{c['pngCompression']}\n（0~9，数值越大 体积越小 画质越差）")
        elif c["saveExt"] == 1:
            self.strSave.set(
                f"保存为 .jpg\n质量：{c['jpegQuality']}\n（0~100，数值越小 体积越小 画质越差）")

        self.optFrame.pack_propagate(True)
        self.optFrame.update()  # 强制刷新
        rH = self.optFrame.winfo_height()  # 由组件撑起的 框架高度
        self.optCanvas.config(scrollregion=(0, 0, 0, rH))  # 画布内高度为框架高度
        self.optFrame.pack_propagate(False)  # 禁用框架自动宽高调整
        self.optFrame["height"] = rH  # 手动还原高度。一次性设置，之后无需再管。

    def openCtrlWin(self):  # 打开参数配置窗口
        if not self.isRunning == 0:
            return
        defaultPath = ""
        if self.imgDict:
            defaultPath = next(iter(self.imgDict.values()))["path"]
        # self.win.attributes("-disabled", 1)  # 禁用父窗口
        imgEditWin(self.closeCtrlWin, defaultPath)

    def closeCtrlWin(self):  # 关闭选择区域，获取选择区域数据
        self.loadConfig()  # 加载参数
        # self.win.attributes("-disabled", 0)  # 启用父窗口

    # 表格操作 ===============================================

    def clearTable(self):  # 清空表格
        if not self.isRunning == 0:
            return
        self.progressbar["value"] = 0
        self.labelPercentage["text"] = "0%"
        self.labelFractions["text"] = "0/0"
        self.labelTime["text"] = "0s"
        self.imgDict = {}
        chi = self.table.get_children()
        for i in chi:
            self.table.delete(i)  # 表格组件移除

    def delImgList(self):  # 图片列表中删除选中
        if not self.isRunning == 0:
            return
        chi = self.table.selection()
        for i in chi:
            self.table.delete(i)
            del self.imgDict[i]  # 字典删除

    def setRunning(self, r):  # 设置运行状态。0停止，1运行中，2停止中
        self.isRunning = r
        if r == 0:
            self.btnRun["text"] = "开始任务"
            self.btnRun['state'] = "normal"
        elif r == 1:
            self.btnRun["text"] = "停止任务"
            self.btnRun['state'] = "normal"
        elif r == 2:
            self.btnRun["text"] = "正在停止"
            self.btnRun['state'] = "disable"

    def run(self):  # 开始任务，创建新线程和事件循环
        if self.isRunning == 0:  # 未在运行，开始运行
            if not self.imgDict:
                return
            # 创建输出文件夹
            p = next(iter(self.imgDict.values()))["path"]
            outFolder = os.path.abspath(os.path.join(p, os.pardir)
                                        ) + "\\" + self.strOutFolder.get()
            if not os.path.isdir(outFolder):
                try:
                    os.makedirs(outFolder)  # 创建
                except Exception as e:
                    tk.messagebox.showerror(
                        '遇到了一点小问题', f'创建输出文件夹失败，请检查格式和权限。文件地址：\n{outFolder}\n\n错误信息：\n{e}')
                    return
            self.setRunning(1)
            # 在当前线程下创建事件循环，在start_loop里面启动它
            newLoop = asyncio.new_event_loop()
            # 通过当前线程开启新的线程去启动事件循环
            threading.Thread(target=self.getLoop, args=(newLoop,)).start()
            # 在新线程中事件循环不断“游走”执行
            asyncio.run_coroutine_threadsafe(self.run_(), newLoop)
        elif self.isRunning == 1:  # 正在运行，停止运行
            self.setRunning(2)

    def getLoop(self, loop):  # 获取事件循环
        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def run_(self):  # 异步，执行任务
        self.labelPercentage["text"] = "初始化"
        p = next(iter(self.imgDict.values()))["path"]
        outFolder = os.path.abspath(os.path.join(p, os.pardir)
                                    ) + "\\" + self.strOutFolder.get()

        def close():  # 关闭所有异步相关的东西
            self.loop.stop()  # 关闭异步事件循环
            self.setRunning(0)
            self.labelPercentage["text"] = "已终止"

        # 初始化UI
        for key in self.imgDict.keys():  # 清空表格参数
            self.table.set(key, column='time', value="")
        allNum, nowNum = len(self.imgDict), 0
        startTime = time.time()  # 开始时间
        costTime = 0
        self.progressbar["maximum"] = allNum
        self.progressbar["value"] = 0
        self.labelPercentage["text"] = "0%"
        self.labelFractions["text"] = f"0/{allNum}"
        self.labelTime["text"] = "0s"
        # 主任务循环
        for key, value in self.imgDict.items():
            # try:
            if not self.isRunning == 1:  # 需要停止
                close()
                return
            name = os.path.splitext(value["name"])[0]
            # print(name)
            Prossing.work(value["path"])  # 处理
            Prossing.save(outFolder, name)  # 保存
            # 刷新UI
            nowNum += 1
            costTimeNow = time.time() - startTime  # 当前总花费时间
            needTimeStr = str(costTimeNow-costTime)  # 单个花费时间
            costTime = round(costTimeNow, 2)  # 刷新花费时间
            self.progressbar["value"] = nowNum
            self.labelPercentage["text"] = f"{round((nowNum/allNum)*100)}%"
            self.labelFractions["text"] = f"{nowNum}/{allNum}"
            self.labelTime["text"] = f"{costTime}s"
            self.table.set(key, column='time',
                           value=needTimeStr[:4])  # 时间写入表格
            # except Exception as e:
            #     tk.messagebox.showerror(
            #         '遇到了亿点小问题', f'图片处理异常：\n{value["name"]}\n异常信息：\n{e}')
        # 结束
        close()  # 完成后关闭
        self.labelPercentage["text"] = "完成！"

    def openProjectWeb(self, e=None):  # 打开项目网页
        webOpen(ProjectWeb)

    def onClose(self):  # 关闭窗口事件
        if self.isRunning == 0:  # 未在运行
            self.win.destroy()  # 直接关闭
        if not self.isRunning == 0:  # 正在运行，需要停止
            self.setRunning(2)
            # self.win.after( # 非阻塞弹出提示框
            #     0, lambda: tk.messagebox.showinfo('请稍候', '等待进程终止，程序稍后将关闭'))
            self.win.after(50, self.waitClose)  # 等待关闭，50ms轮询一次是否已结束子进程

    def waitClose(self):  # 等待进程关闭后销毁窗口
        if self.isRunning == 0:
            self.win.destroy()  # 销毁窗口
        else:
            self.win.after(50, self.waitClose)  # 等待关闭，50ms轮询一次是否已结束子进程


if __name__ == "__main__":
    Win()

# pyinstaller -F -w -i icon/icon.ico -n "Umi-CUT 批量图片去黑边" main.py
