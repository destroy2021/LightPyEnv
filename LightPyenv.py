import ctypes
import os
import argparse
import winreg as reg
import RegConfig
import re
import subprocess
import winshell
from termcolor import colored

envDirName = ".lightPyenv"
config = RegConfig.RegConfig("LightPyenv")

reg_currentPython = "currentPython"
reg_envPath = "envPath"
reg_pythonsDir = "pythonsDir"
def isRunByAdmin():
	return ctypes.windll.shell32.IsUserAnAdmin()


# 创建快捷方式
def create_shortcut(target_path, source_path, description="", icon=None):
    with winshell.shortcut() as shortcut:
        shortcut.path = source_path          # 目标文件的路径
        shortcut.description = description   # 快捷方式描述
        if icon:
            shortcut.icon_location = (icon, 0)  # 图标路径，可以不设置，默认使用目标文件的图标
        shortcut.write(target_path.replace(".exe",".lnk"))                     # 写入快捷方式文件

def create_bat(target_path, source_path):
    with open(target_path,"w+",encoding="utf-8") as bat:
        s = f"""
@echo off
{source_path} %*
        """
        bat.write(s)

def uninstall():
    if isRunByAdmin() == 0:
        print("请使用管理员运行此命令")
        return
    envPath = config.getConfig(reg_envPath)
    if envPath is None:
        return
    try:
        os.rmdir(envPath)
        config.clearConfig()
    except Exception as e:
        print(f"Uninstall Error: {e}")
        return


def install():
    if isRunByAdmin() == 0:
        print("请使用管理员运行此命令")
        os.system("pause")
        exit(0)

    try:
        try:
            os.mkdir(envDirName)
        except FileExistsError:
            print(f"{envDirName} exist")
        envPath = os.path.join(os.getcwd(),envDirName)
        RegConfig.addOrRemoveGlobalEnvironment(envPath)
        config.setConfig(reg_envPath,envPath)
    except Exception as e:
        print(f"Install Error: {e}")

def findFile(directory, filename, use_regex : bool = False) -> os.DirEntry:
    with os.scandir(directory) as it:
        dirs = []

        #先遍历文件
        for entry in it:
            if entry.is_file():
                #使用正则匹配
                if use_regex and re.match(filename,entry.name) != None:
                    return entry
                elif entry.name == filename:
                    return entry
            elif entry.is_dir():
                dirs.append(entry)

        #后遍历文件夹
        for entry in dirs:
            if entry.name == filename:
                return result
            # 递归查找子文件夹
            result = findFile(entry.path, filename ,use_regex)
            if result:
                return result

    return False
def listPython(path):
    pythonDirs = []
    for pythonDir in os.scandir(path):
        py = findFile(pythonDir.path,"python.exe")
        if py == False:
            py = findFile(pythonDir.path,"python3.exe")
        if py == False:
            py = findFile(pythonDir.path, "python2.exe")
        if py == False:
            print(f"dir {pythonDir} has no python installed")
            continue
        pip = findFile(pythonDir.path, "pip.exe")
        if pip == False:
            pip = findFile(pythonDir.path, "pip2.exe")
        if pip == False:
            pip = findFile(pythonDir.path, "pip3.exe")
        if pip == False:
            print(f"dir {pythonDir} has no pip installed")
            continue
        version = subprocess.getoutput(f"{py.path} -V")
        pydir = py.path.replace(py.name, "")
        pipdir = pip.path.replace(pip.name, "")

        pythonDirs.append({
            "version" : version,
            "pythonDir" : pythonDir,
            "python" : py,
            "pip" : pip,
            "pydir" : pydir,
            "pipdir" : pipdir,
        })
    pythonsDir = config.getConfig(reg_pythonsDir)
    print(f"当前pythons 目录: {pythonsDir}")
    envPath = config.getConfig(reg_envPath)
    print(f"当前env目录: {envPath} \n")
    print("Python Versions: ")
    currentPython = config.getConfig(reg_currentPython)
    for pythonDir in pythonDirs:
        if currentPython == pythonDir['pythonDir'].name:
            print(f">>>> \t{pythonDir['pythonDir'].name} --> {pythonDir['version']} => {pythonDir['python'].path}")
        else:
            print(f"\t{pythonDir['pythonDir'].name} --> {pythonDir['version']} => {pythonDir['python'].path}")
    print("\n")
    return pythonDirs

def changePython(pythonVersion):
    envPath = config.getConfig(reg_envPath)
    if envPath == False:
        print("changePython failed: 还没有执行install")
        return False
    pythonsDir = config.getConfig(reg_pythonsDir)
    if pythonsDir == False:
        print("changePython failed: 还没有设置pythons 目录")
        return False
    pythonDirs = listPython(pythonsDir)
    isFind = False
    for pythonDir in pythonDirs:
        if pythonDir['pythonDir'].name == pythonVersion:
            isFind = True
            targetPath = os.path.join(envPath,"python.bat")
            sourcePath = os.path.join(pythonDir['python'].path)
            create_bat(targetPath,sourcePath)

            sourcePath = os.path.join(pythonDir['pip'].path)
            targetPath = os.path.join(envPath,"pip.bat")
            create_bat(targetPath,sourcePath)

            if "Python 2" in pythonDir['version']:
                sourcePath = os.path.join(pythonDir['python'].path)
                targetPath = os.path.join(envPath,"python2.bat")
                create_bat(targetPath,sourcePath)

                sourcePath = os.path.join(pythonDir['pip'].path)
                targetPath = os.path.join(envPath,"pip2.bat")
                create_bat(targetPath,sourcePath)
            else:
                sourcePath = os.path.join(pythonDir['python'].path)
                targetPath = os.path.join(envPath,"python3.bat")
                create_bat(targetPath,sourcePath)

                sourcePath = os.path.join(pythonDir['pip'].path)
                targetPath = os.path.join(envPath,"pip3.bat")
                create_bat(targetPath,sourcePath)
    if isFind:
        config.setConfig(reg_currentPython,pythonVersion)
        print(f"成功切换python版本为 {pythonVersion} ")
        os.system("python -V")
        os.system("pip -V")
    else:
        print(f"没有找到版本 {pythonVersion}")
    return isFind

# def setLocalEnvironment(pythonVersion):
#     pythonsDir = config.getConfig(reg_pythonsDir)
#     if pythonsDir:
#         pythonDirs = listPython(pythonsDir)
#     else:
#         print("请设置pythons 目录")
#         return False
#     for pythonDir in pythonDirs:
#         if pythonDir['pythonDir'].name == pythonVersion:
#             os.system(f"set PATH=\"{pythonDir['pydir']};%path%\"")
#             os.system(f"set PATH=\"{pythonDir['pipdir']};%path%\"")
#             break


def bank():
    result = """
 __        __            __          __      _______                                           
/  |      /  |          /  |        /  |    /       \                                          
$$ |      $$/   ______  $$ |____   _$$ |_   $$$$$$$  | __    __   ______   _______   __     __ 
$$ |      /  | /      \ $$      \ / $$   |  $$ |__$$ |/  |  /  | /      \ /       \ /  \   /  |
$$ |      $$ |/$$$$$$  |$$$$$$$  |$$$$$$/   $$    $$/ $$ |  $$ |/$$$$$$  |$$$$$$$  |$$  \ /$$/ 
$$ |      $$ |$$ |  $$ |$$ |  $$ |  $$ | __ $$$$$$$/  $$ |  $$ |$$    $$ |$$ |  $$ | $$  /$$/  
$$ |_____ $$ |$$ \__$$ |$$ |  $$ |  $$ |/  |$$ |      $$ \__$$ |$$$$$$$$/ $$ |  $$ |  $$ $$/   
$$       |$$ |$$    $$ |$$ |  $$ |  $$  $$/ $$ |      $$    $$ |$$       |$$ |  $$ |   $$$/    
$$$$$$$$/ $$/  $$$$$$$ |$$/   $$/    $$$$/  $$/        $$$$$$$ | $$$$$$$/ $$/   $$/     $/     
              /  \__$$ |                              /  \__$$ |                               
              $$    $$/                               $$    $$/                                
               $$$$$$/                                 $$$$$$/                                 
"""
    result = colored(result, 'green')
    print(result)
def main():
    bank()
    parser = argparse.ArgumentParser(description="LightPyenv For Windows是一款轻量级随时切换python版本的程序，参考Pyenv程序设计")
    parser.add_argument("--install",action="store_true",help="[管理员权限运行]配置环境变量")
    parser.add_argument("--uninstall",action="store_true",help="[管理员权限运行]删除配置注册表以及环境变量")
    parser.add_argument("--list",action="store_true",help="查看可切换python版本")
    parser.add_argument("-p","--path",default=None,type=str,help="选择已存在的python目录，会遍历目录下所有python版本")
    parser.add_argument("-g","--globals",default=None,type=str,help="全局切换python版本")
    args = parser.parse_args()
    if args.install:
        install()
    if args.uninstall:
        uninstall()
    if args.list:
        pythonsDir = config.getConfig(reg_pythonsDir)
        if pythonsDir:
            listPython(pythonsDir)
        else:
            print("请设置pythons 目录")
    if args.path is not None:
        if config.setConfig(reg_pythonsDir,args.path):
            print(f"set {reg_pythonsDir} to {args.path}")
    if args.globals is not None:
        changePython(args.globals)


if __name__ == "__main__":
    main()