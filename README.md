# 本地无网络环境下的截图OCR和截图翻译
<h1>2.0版本</h1>
修复了在1.0版本中调用截图方法时一直生成新线程而不销毁的bug </br>
增加运行的好好的可能中途退出的bug（解决方案1?：创建一个新的py文件（launch.py），每10秒检测一次是否启动，没有则启动程序）半解决</br>
期望下个版本可以修复这个问题
<h1>1.0版本</h1>
该脚本通过Tesseract-OCR和argostranslate实现在本地无网络的环境下截图ocr提取文字和截图翻译功能</br>
支持中英互译和ocr功能，有其他语言需求自行修改代码 </br>
<h1>注意事项：</h1>
使用该脚本需要安装Tesseract-OCR（文字识别包）和argostranslate（翻译包） </br>
Tesseract-OCR语言文件下载地址：https://github.com/tesseract-ocr/tessdata  文件后缀为.traineddata</br>
argostranslate安装翻译包需要梯子，不然可能无法下载  （可以安装argostranslate的GUI界面来快捷下载所需语言包）</br>
该脚本通过监听键盘按键来进行上述功能（程序运行时需进行ocr和翻译的初始化 所以一开始可能没有动静，等待几秒在按下组合键）
