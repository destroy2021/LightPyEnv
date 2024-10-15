今天下载了个Pyenv来管理Python多版本，结果弄了半天弄不好，管理员权限运行的python版本和非管理员权限运行的python版本还能不一样
一怒之下耗费半天时间写了这个轻量级的管理工具，支持管理多个版本Python

使用方法：
LightPyEnv -h
LightPyEnv --install    #初始化
LightPyEnv -p D:\Python    #你的所有Python版本需要放在同一个目录下
LightPyEnv -g Python311    #Python311是在Python目录下的 目录名称
