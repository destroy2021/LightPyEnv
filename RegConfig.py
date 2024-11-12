import winreg as reg

class RegConfig:
    def __init__(self,configName : str, configRegName : str = None):
        self.__configName = configName
        self.__configRegName = configRegName
        if configRegName is None:
            self.__configRegName = configName
        self.createConfigIfNotExist()

    def createConfigIfNotExist(self):
        try:
            _ = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\{self.__configRegName}", 0, reg.KEY_READ)
        except FileNotFoundError:
            try:
                softwareKey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, f"SOFTWARE", 0, reg.KEY_READ)
                ret = reg.CreateKey(softwareKey, self.__configRegName)
                reg.CloseKey(softwareKey)
            except Exception as e:
                print(f"createConfigIfNotExist Error: {e}")
                return False
            return ret

    def getConfig(self,keyName):
        try:
            configKey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\{self.__configRegName}", 0, reg.KEY_READ)
            ret,_ = reg.QueryValueEx(configKey, keyName)
            reg.CloseKey(configKey)
        except FileNotFoundError:
            # print("getConfig failed 无法找到注册表配置")
            return False
        except Exception as e:
            print(f"getConfig Error: {e}")
            return False
        return ret

    def setConfig(self,keyName, value, type=reg.REG_SZ) -> bool:
        try:
            configKey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\{self.__configRegName}", 0, reg.KEY_READ | reg.KEY_WRITE)
            reg.SetValueEx(configKey, keyName,0, type, value)
            reg.CloseKey(configKey)
            return True
        except FileNotFoundError:
            print("setConfig failed 无法找到注册表配置")
        except Exception as e:
            print(f"setConfig Error: {e}")
        return False
    # 删除配置注册表
    def clearConfig(self) -> bool:
        try:
            softwareKey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, "SOFTWARE", 0, reg.KEY_READ | reg.KEY_WRITE)
            reg.DeleteKey(softwareKey, self.__configRegName)
            reg.CloseKey(softwareKey)
            print("已删除注册表配置")
            return True
        except FileNotFoundError:
            print("无法找到注册表配置")
        except Exception as e:
            print(f"clearConfig Error: {e}")
        return False

# oper = 1 添加，oper = 0 移除，系统环境变量Path
def addOrRemoveGlobalEnvironment(new_path: str, oper: int = 1,python_path = "python"):
    # 注册表路径
    reg_path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    isOper = False
    isNotify = False
    try:
        # 打开注册表的系统环境变量部分
        reg_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, reg_path, 0, reg.KEY_SET_VALUE | reg.KEY_READ)
        # 获取当前的 PATH 变量
        current_path, _ = reg.QueryValueEx(reg_key, 'Path')

        # 确保每个path以;结尾
        if current_path.endswith(";") is not True:
            current_path += ";"
        # 将环境变量分割
        current_path_list = current_path.split(";")

        if new_path.endswith(';'):
            new_path = new_path[:-1]

        index = -1
        if python_path is not False and python_path != "":
            # 寻找是否有自定义python目录存在
            for i in range(len(current_path_list)):
                if python_path.lower() in current_path_list[i].lower():
                    index = i
                    break

        # oper == 1表示添加，0 删除
        if oper == 1:
            if new_path not in current_path:
                # 没有自定义python路径，则添加到末尾
                if index == -1:
                    current_path_list.append(new_path)
                else:
                    # 如果找到自定义的python路径，则添加到他前面
                    current_path_list.insert(index, new_path)
            else:
                print(f"Warning: {new_path} is already in the system PATH.")
        else:
            isRemoveKey = False
            for i in range(len(current_path_list)):
                if new_path == current_path_list[i]:
                    current_path_list[i] = ""
                    isRemoveKey = True
            if isRemoveKey is not True:
                print(f"Warning: Maybe already remove {new_path} from System PATH?")

        new_path_value = ""
        for path in current_path_list:
            if path == "":
                continue
            new_path_value += path
            new_path_value += ";"

        if new_path_value == "":
            print("Error: The new PATH is Empty")
            reg.CloseKey(reg_key)
            return False

        reg.SetValueEx(reg_key, 'Path', 0, reg.REG_EXPAND_SZ, new_path_value)
        print("Success set System Path Reg Value")
        reg.CloseKey(reg_key)
        isOper = True
        # 通知系统环境变量已更新（通过广播通知系统）
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment',
                                                          SMTO_ABORTIFHUNG, 5000)
        if result:
            print("System has been notified about the PATH change.")
            isNotify = True
        else:
            print("Failed to notify the system about the PATH change.")
    except PermissionError:
        print("You need to run this script as an administrator to modify system environment variables.")
    except Exception as e:
        print(f"Error: {e}")
    return isOper and isNotify