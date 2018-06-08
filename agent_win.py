# _*_coding:utf-8_*_
__author__ = 'ju'

import platform
import os
import psutil
import json
import socket
import time
import datetime
import sys


# 配置文件路径
def get_path():
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_path, "config.json")
    return file_path


# 读取配置
def get_config():
    file_path = get_path()
    if os.path.exists(file_path):
        with open(file_path, encoding='utf8') as f:
            result = json.loads(f.read())
        return result


# 解析数据包
def unpack_data(data):
    data_dict = {}
    data_attrs_list = [i for i in dir(data) if not i.startswith('_')]
    for i in data_attrs_list:
        if i != 'index':
            if i != 'count':
                data_dict[i] = getattr(data, i)
    return data_dict


def getOS():
    content = platform.platform()
    return content


# 'CLUSTER'
def getCpu():
    data = {"cores": {},
            "all_cpu_usage": {},
            "cpu_model": '',
            "cpu_num": int()
            }
    try:
        data['cpu_num'] = psutil.cpu_count()
        content = os.popen("wmic cpu get Name").read()
        list_content = [i for i in content.splitlines() if len(i) > 0]
        data["cpu_model"] = list_content[1]

        ccc = psutil.cpu_stats()
        all_cpu = psutil.cpu_times_percent()
        data["all_cpu_usage"] = unpack_data(all_cpu)

        per_cpu = psutil.cpu_times_percent(percpu=True)
        i = 1
        for per in per_cpu:
            data["cores"]["core_" + str(i)] = unpack_data(per)
            i += 1
    except Exception as e:
        print("cpu_error:", e)
    return data


def getHostName():
    content = platform.node()
    return content


def getUptime():
    startUnixTime = psutil.boot_time()
    nowUnixTime = time.time()
    rangeUnixTime = nowUnixTime - startUnixTime
    online_time = time.strftime("%H:%M:%S", time.gmtime(rangeUnixTime))
    if rangeUnixTime > 24 * 60 * 60:
        a = str(int(rangeUnixTime / (24 * 60 * 60)))
        if len(a) < 2:
            online_time = "0" + a + " " + online_time
        else:
            online_time = a + " " + online_time

    return online_time


def getMemInfo():
    mem_dict = {}
    try:
        data = psutil.virtual_memory()

        mem_dict["mem_total"] = data.total
        mem_dict["mem_free"] = data.free

        swap_data = psutil.swap_memory()
        mem_dict["swap_free"] = swap_data.free
        mem_dict["swap_total"] = swap_data.total
    except Exception as e:
        print("mem_error:", e)
    return mem_dict


def getLocalDiskPart():
    disk_part = {}
    try:
        content = psutil.disk_partitions()

        for part in content:
            disk_part[part.device] = {}
            if part.opts == "cdrom":
                #disk_part[part.device] = "CDROM"
                disk_part[part.device]["total"] = 0
                disk_part[part.device]["available"] = 0
                disk_part[part.device]["used"] = 0
                disk_part[part.device]["fs"] = 0
            else:
                disk_use = psutil.disk_usage(part.device)
                disk_part[part.device]["total"] = disk_use.total
                disk_part[part.device]["available"] = disk_use.free
                disk_part[part.device]["used"] = disk_use.used
                disk_part[part.device]["fs"] = part.fstype
                disk_part[part.device]["percent"] = disk_use.used / disk_use.total

    except Exception as e:
        print("disk_error:", e)
    return disk_part


def getNetworkInfo():
    NET = {
        "rx": {},
        "tx": {}
    }
    try:
        content = psutil.net_io_counters()
        NET["rx"]["LocalConnection"] = content.bytes_recv
        NET["tx"]["LocalConnection"] = content.bytes_sent
    except Exception as e:
        print("net_error:", e)

    return NET


def getLoadInfo():
    """ Returns a list CPU Loads"""

    try:
        result1 = psutil.cpu_percent(0.1)
        result2 = psutil.cpu_percent(0.5)
        result3 = psutil.cpu_percent(1.5)
        load = {"1min": result1, "5min": result2, "15min": result3}
    except Exception as e:
        load = {"1min": 0, "5min": 0, "15min": 0}

    return load

def getProcess():
    process_part = {}
    try:
        for part in psutil.process_iter():
            process_part[part.pid] = {}
            try:
                # proc = psutil.Process(part)
                try:
                    process_part[part.pid]["name"] = part.name()
                    process_part[part.pid]["cmd"] = part.exe()
                    process_part[part.pid]["start"] = datetime.datetime.fromtimestamp(part.create_time()).strftime("%Y/%m/%d %H:%M:%S")
                    process_part[part.pid]["cpu"] = part.cpu_percent(interval=0)
                    process_part[part.pid]["memory"] = round(part.memory_info().rss/1024, 2)
                    process_part[part.pid]["username"] = part.username()
                except psutil.AccessDenied as ad:
                    del process_part[part.pid]
            except psutil.NoSuchProcess as pid:
                print("no process found with pid=%s" % pid)
    except Exception as e:
        print("process_error:", e)
    return process_part

def monitor(clusterName="win_PC"):
    data = {"OS": '',
            "CLUSTER": '',
            "HOSTNAME": '',
            "CPU": {},
            "NET": {},
            "LOCALDISKPART": {},
            "MEM": {},
            "LOAD": {},
            "UPTIME": {},
            "PROCESS": {}
            }

    data["OS"] = getOS()
    data["CLUSTER"] = clusterName
    data["HOSTNAME"] = getHostName()
    data["CPU"] = getCpu()
    data["NET"] = getNetworkInfo()
    data["LOCALDISKPART"] = getLocalDiskPart()
    data["MEM"] = getMemInfo()
    data["LOAD"] = getLoadInfo()
    data["UPTIME"] = getUptime()
    data["PROCESS"] = getProcess()

    json_data = json.dumps(data, ensure_ascii=False)
    return json_data + '\n'


if __name__ == "__main__":
    agentCfg = get_config()
    nodeName = agentCfg["groupName"]
    while True:
        jsonString = monitor(nodeName)
        print(jsonString)
        time.sleep(5)
