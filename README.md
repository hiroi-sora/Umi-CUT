# Umi-CUT 批量图片去黑边/裁剪/压缩软件

批量处理图片文件，具有范围裁剪、自动去除黑边、调整大小、压缩体积等功能。

![](https://tupian.li/images/2022/04/15/image.png)
![](https://tupian.li/images/2022/04/15/image5f088a54bf9e3163.png)

## 下载

[Umi-CUT 批量图片转文字 v1.0.0](https://github.com/hiroi-sora/Umi-CUT/releases/tag/v1.0)

## 系统支持

- 源码可在绝大多数支持Python 3.x和Opencv的平台上跑起来。
- 发行版exe程序：
  - 支持 win10 x64 。
  - 支持 win7 x64 sp1 及以上版本。若您无法打开本软件，请检查是否已打系统补丁 KB2533623 、KB2999226 。

## Umi-系列图片处理软件

[Umi-OCR 批量图片转文字软件](https://github.com/hiroi-sora/Umi-OCR)
**Umi-CUT 批量图片去黑边/裁剪/压缩软件 ◁**

## 简介

本软件能批量处理本地图片，具有范围裁剪、自动去除黑边、调整大小、压缩体积等功能。
通过范围裁剪和去黑边两种功能配合，可以绕过图片边缘的干扰色块，提取图片中部的所需内容。

> 比如下图这张Ipad截图，底部带有小白条，普通去黑边工具无法很好的去除底部黑边。
> ![](https://s1.ax1x.com/2022/04/15/L8GDRP.png)
> 
> 而 Umi-CUT 可以先设置手动范围，绕过小白条，再自动去除剩下的纯黑边框。只需设定一次，便可批量处理所有同类图片。这是开发本软件的初衷。


## 使用说明

### 准备

发行包用户：下载压缩包并解压。
Python用户：下载源码，安装好Opencv等所需模块。

### 一键去除黑边

1. 打开主程序，将任意 **图片/文件夹** 拖入窗口中的白色背景表格区域，或点击左上方的 **浏览** 选择图片。
2. 点击右上方 **开始任务** ，等待进度条走完。
   - 任务进行中，可随时点击 **终止任务**（原开始任务按钮）来停止，但下次开始时依然会从头开始。
3. 在 **第一张图片的目录** 下的 `# 裁剪` 文件夹查看输出图片。

![](https://s1.ax1x.com/2022/04/15/L8YDu8.png)

### 其他参数设置

点击 **设置** 选项卡，点击 **参数设置** 打开配置窗口。根据提示调整参数即可。
- 红色框为手段裁剪的范围。虚线框是在手动裁剪基础上，自动去除黑边的范围。
- 若待处理图片的黑边中含有少量杂色、噪点，调高`中值滤波`参数。（但滤波值太高可能导致留下很窄的黑边）
- 若待处理图片的黑边不是纯“黑”，调高`阈值`参数。（但阈值太高可能导致需要保留的部分也被裁剪）

![](https://tupian.li/images/2022/04/15/imagef816383a8800731b.png)

## 测试

输入100张2k分辨率图片。
输出为png图片时，平均每张0.5s。
输出为jpg图片时，平均每张0.2s。

## 开发说明

- 使用`pyinstaller`打包，参数为
  ```pyinstaller -F -w -i icon/icon.ico -n "Umi-CUT 批量图片去黑边" main.py```

## 更新日志

##### v1.0.0 `2022.4.15`