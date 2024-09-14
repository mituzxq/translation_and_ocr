# translation_and_ocr
该脚本通过Tesseract-OCR和argostranslate实现在本地无网络的环境下截图ocr提取文字和截图翻译功能</br>
注意事项： </br>
使用该脚本需要安装Tesseract-OCR（文字识别包）和argostranslate（翻译包） </br>
Tesseract-OCR语言文件下载地址：https://github.com/tesseract-ocr/tessdata  文件后缀为.traineddata</br>
argostranslate安装翻译包需要梯子，不然可能无法下载  （可以安装argostranslate的GUI界面来快捷下载所需语言包）</br>
该脚本通过监听键盘按键来进行上述功能（程序运行时需进行ocr和翻译的初始化 所以一开始可能没有动静，等待几秒在按下组合键）
