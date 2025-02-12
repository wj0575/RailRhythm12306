# Rail Rhythm 中国铁路时刻表查询工具
# wj_0575 2025.1
import os.path

import requests
import json

from datetime import datetime
current_date = datetime.now()
auto_date = current_date.strftime("%Y-%m-%d")
auto_date_1 = auto_date.replace("-","")
# 这是默认时间参数
# 12306一个系统居然有两种表示日期的方法

train_list = {} # reference from train_no to detailed information
no_list = {} # reference from train code to train_no

headers = {
    "Accept":"*/*",
    "Connection":"keep-alive",
    "Origin":"https://kyfw.12306.cn",
    "Referer":"https://kyfw.12306.cn/",
    "Sec-Fetch-Dest":"empty",
    "Sec-Fetch-Mode":"cors",
    "Sec-Fetch-Site":"same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
}

def time_interval(time_start, time_end):
    """计算时间间隔的函数"""
    start_hour = int(time_start[0:2])
    start_minute = int(time_start[3:5])
    end_hour = int(time_end[0:2])
    end_minute = int(time_end[3:5])
    start_total = start_hour * 60 + start_minute
    end_total = end_hour * 60 + end_minute
    if end_total >= start_total:
        interval = end_total - start_total
    else:
        interval = 24 * 60 - start_total + end_total
    return interval

def print_train(x):
    """这个函数用于输出一个车次的信息
    参数x为一个字典"""
    code = x[0]["station_train_code"]
    callback = {}
    print(code,end=' ')
    for i in x:
        if i["station_train_code"] != code:
            print("/", i["station_train_code"], end='')
            break
    print(" ",x[0]["train_class_name"], "\t", x[0]["start_station_name"], "-",
          x[0]["end_station_name"])
    d = "0"
    for i in x:
        print(i["station_no"]+" "+i["station_name"].ljust(5,' ')+'\t',
              i["arrive_time"].ljust(7,' '),end='')
        if "is_start" in i:
            print(i["start_time"].ljust(5,' '),end='')
        elif i["stop_time"] == 0:
            print("----        ",end='')
        else:
            print(i["start_time"].ljust(5,' ')+str(i["stop_time"]).rjust(4,' ')+'\'',end='  ')
        callback[i["station_no"]] = "Station "+i["station_name"]
        if i["arrive_day_diff"] != d:
            d = i["arrive_day_diff"]
            print("Day",int(d)+1,end="  ")
        if i["station_train_code"] != code:
            code = i["station_train_code"]
            print("switch to",code,end="  ")
        print("",end="\n")
    for i in x:
        for j in x:
            if i == j:
                continue
            callback[i["station_no"] + "-" + j["station_no"]] = i["station_name"] + "-" + j["station_name"]
    return callback


def search_station(x, t1='00:00', t2='24:00', sort_order = "", prefix = "GDCKTZSYP"):
    """这个函数用来查找车站的时刻表
    在sort_order中，如果包含up/dn，说明需要显示上/下行车次
    如果包含st/ed/ps，说明需要显示始发/终到/过路车次"""
    sort_order.lower()
    tail = []
    if "up" in sort_order:
        tail.extend(list("24680"))
    if "dn" in sort_order:
        tail.extend(list("13579"))
    if len(tail) == 0:
        tail = list("1234567890")
    st = "st" in sort_order
    ed = "ed" in sort_order
    ps = "ps" in sort_order
    if st == False and ed == False and ps == False:
        st = ed = ps = True
    table = {}
    cnt = 0
    visible = 0
    for i in train_list:
        for j in train_list[i]:
            if j["station_name"] == x and j["start_time"] >= t1 and j["start_time"] <= t2:
                table[j["start_time"]+str(cnt)] = {
                    "code": j["station_train_code"],
                    "start_time": j["start_time"],
                    "arrive_time": j["arrive_time"],
                    "stop_time": j["stop_time"],
                    "st": train_list[i][0]["start_station_name"],
                    "ed": train_list[i][0]["end_station_name"],
                    "class": train_list[i][0]["train_class_name"]
                }
                cnt += 1
    print(x, '\t', t1, '-', t2, "\t", cnt, "results")
    callback = {}
    for i in sorted(table.keys()):
        if (table[i]["code"][-1:] in tail) == False:
            continue
        if (("P" in prefix and table[i]["code"][0].isdigit or table[i]["code"][0] in prefix) == False):
            continue
        if table[i]["st"] == x:
            if st == False:
                continue
            status = 'ST '
        elif table[i]["ed"] == x:
            if ed == False:
                continue
            status = 'ED '
        else:
            if ps == False:
                continue
            status = str(table[i]["stop_time"]).rjust(2,' ')+"\'"
        visible += 1
        print(str(visible).ljust(4,' '), table[i]["code"].ljust(7,' '),
              table[i]["arrive_time"].ljust(7,' '), end=' ')
        callback[str(visible)] = "."+table[i]["code"]
        if(status == 'ED '):
            print("----        ", table[i]["st"], '-', table[i]["ed"], table[i]["class"], status)
        elif status == 'ST ':
            print(table[i]["start_time"].ljust(7, ' '), "    ", table[i]["st"], '-',
                  table[i]["ed"], table[i]["class"], status)
        else:
            print(table[i]["start_time"].ljust(5,' '), str(table[i]["stop_time"]).rjust(4,' ')+'\' ',
                  table[i]["st"],'-',table[i]["ed"],table[i]["class"])
    print(x, '\t', cnt, "results,", visible, "visible:",end=' ')
    if st:
        print("ST", end=' ')
    if ed:
        print("ED", end=' ')
    if ps:
        print("PS", end=' ')
    if "2" in tail:
        print("UP", end=' ')
    if "1" in tail:
        print("DN", end=' ')
    print(" ")
    return callback

def search_link(st, ed, sort_order = "st", prefix = "GDCKTZSYP"):
    callback = {}
    if len(set(st) & set(ed)) > 0:
        print("The set of starting and ending stations include same element")
        return {}
    table = {}
    list_st = {}
    list_ed = {}
    cnt = 0
    visible = 0
    index = {}
    for i in train_list:
        for j in train_list[i]:
            if j["station_name"] in st and ((i in list_st) == False):
                list_st[i] = j
            if j["station_name"] in ed and ((i in list_ed) == False):
                list_ed[i] = j
    for i in list_st:
        if i in list_ed and int(list_st[i]["station_no"]) < int(list_ed[i]["station_no"]):
            cnt += 1
            t1 = list_ed[i]["running_time"]
            t2 = list_st[i]["running_time"]
            delta_t = int(t1[0:2]) * 60 + int(t1[3:5]) - int(t2[0:2]) * 60 - int(t2[3:5]) - list_st[i]["stop_time"]
            code = list_st[i]["station_train_code"]
            info = train_list[no_list[code]][0]
            table[code] = {
                "code": code,
                "time": str(delta_t // 60) + ":" + str(delta_t % 60 // 10) + str(delta_t % 60 % 10),
                "start_time": list_st[i]["start_time"],
                "arrive_time": list_ed[i]["arrive_time"],
                "st": list_st[i]["station_name"],
                "ed": list_ed[i]["station_name"],
                "start_station": info["start_station_name"],
                "end_station": info["end_station_name"],
                "class": info["train_class_name"]
            }
            if "v" in sort_order:
                index[delta_t * 10000 + cnt] = code
            elif "ed" in sort_order:
                index[list_ed[i]["arrive_time"] + str(cnt)] = code
            else:
                index[list_st[i]["start_time"] + str(cnt)] = code
    for i in st:
        if st[-1] != i:
            print(i + '/', end='')
        else:
            print(i, end=' ')
    print("->", end=' ')
    for j in ed:
        if ed[-1] != j:
            print(j + '/', end='')
        else:
            print(j, end='   ')
    print(cnt, "results")
    for i in sorted(index):
        t = table[index[i]]
        code = t["code"]
        if "P" in prefix and code[0].isdigit or code[0] in prefix:
            visible += 1
            callback[str(visible)] = "." + code
            print(str(visible).ljust(3,' '), t["code"].ljust(6, ' '),
                  t["st"].ljust(5,' ') + "\t" + t["start_time"].ljust(5,' ') + "\t  ",
                  t["ed"].ljust(5,' ') + "\t" + t["arrive_time"].ljust(5,' ') + "\t<", t["time"],">\t",
                  t["start_station"], '-', t["end_station"], t["class"])
    for i in st:
        if st[-1] != i:
            print(i + '/', end='')
        else:
            print(i, end=' ')
    print("->", end=' ')
    for j in ed:
        if ed[-1] != j:
            print(j + '/', end='')
        else:
            print(j, end='   ')
    print(cnt, "results,", visible, "visible")
    return callback



url_train_no = "https://search.12306.cn/search/v1/train/search"
params_train_no = {
    "keyword" : "",
    "date" : ""
    # keyword=G1&date=20250114
}
def get_train_no(x, date=auto_date_1):
    """这个函数用于匹配和查找车次信息
    即train_no编号
    可以查一个也可以查多个
    由于12306一次返回最多200条匹配车次的train_no编号
    所以当输入的车次号数字部分不少于两位的时候
    此函数返回的字典中将包含所有匹配车次的train_no编号
    输入的x是关键字 示例 G1 G10 5"""
    params_train_no["keyword"] = x
    params_train_no["date"] = date
    resp = requests.get(url=url_train_no, params=params_train_no, headers=headers)
    if resp.status_code == 200:
        js = resp.json()
        resp.close()
        if js["data"] == []:
            return ("empty")
        return js["data"]
    else:
        return "error"

url_train_info = "https://kyfw.12306.cn/otn/queryTrainInfo/query"
params_train_info = {
    "leftTicketDTO.train_no" : "",
    "leftTicketDTO.train_date" : "",
    "rand_code" : "",
}
def get_train_info(x, date=auto_date):
    """这个函数用于按照train_no查找具体信息
    返回一个字典"""
    params_train_info["leftTicketDTO.train_no"] = x
    params_train_info["leftTicketDTO.train_date"] = date
    resp = requests.get(url=url_train_info, params=params_train_info, headers=headers)
    if resp.status_code == 200:
        data = resp.json()["data"]["data"]
        resp.close()
        if data is None:
            return "error"
        for sta in data:
            if "is_start" in sta:
                sta["stop_time"] = 0
            else:
                sta["stop_time"] = time_interval(sta["arrive_time"], sta["start_time"])
        return data
    else:
        return "error"


def get_all_info(head):
    cnt = 0
    for num in range(1,100):
        resp = get_train_no(head+str(num))
        print(str(num)+"%", cnt,"piece of data getted")
        if resp == "empty":
            continue
        if resp == "error":
            print("request error when getting related trains of",head+str(num))
            continue
        for i in resp:
            code = i["station_train_code"]
            if (code in no_list) == False:
                no = i["train_no"]
                no_list[code] = no
                if (no in train_list) == False:
                    cnt += 1
                    info = get_train_info(i["train_no"])
                    if info == "error":
                        print("request error when getting train schedule of", i["train_no"])
                        continue
                    else:
                        train_list[no] = info


def count_code():
    print("Train sum:", len(no_list))
    cnt = {'G': 0, 'D': 0, 'C': 0, 'Z': 0, 'T': 0, 'K': 0, 'S': 0, 'Y': 0, 'Pure number': 0, }
    for i in no_list:
        if i[0].isdigit():
            cnt['Pure number'] += 1
        else:
            cnt[i[0]] += 1
    for i in cnt:
        print(i, ":", cnt[i])

s = ""
callback = {} # 跳转数据
trace = {} # 回溯数据
trace_code = 0
trace_max = 0
city_station = {} # 同城车站数据

print("Welcome to the Rail Rhythm railway timetable query tool")
if os.path.exists('city_station.json'):
    with open('city_station.json', 'r') as f1:
        city_station = json.load(f1)
print("Current date setting:", auto_date)
while s != "exit":
    s = input("Input instruction: ")
    s = s.lower()
    if s == "":
        continue
    if s in callback:
        s = callback[s]
    if s[0:6].lower() == "import":
        type = s[-1:].upper()
        if type in ['G', 'D', 'C', 'Z', 'T', 'K', 'S', 'Y']:
            get_all_info(type)
            print(type, "prefix train code information downloaded")
            print(len(train_list), "train numbers in total")
        elif type == 'P':
            get_all_info('')
            print("Pure numerical numbering train information downloaded")
            print(len(train_list), "train numbers in total")
        elif type == 'A':
            for h in ['G', 'D', 'C', 'Z', 'T', 'K', 'S', 'Y','']:
                get_all_info(h)
                if(h == ''):
                    print("Pure numerical numbering train information downloaded")
                else:
                    print(h, "prefix train code information downloaded")
                print(len(train_list), "train numbers in total")
        continue
    if s.lower() == "save":
        with open('train_list' + auto_date_1 + '.json', 'w') as f1:
            json.dump(train_list, f1)
        with open('no_list' + auto_date_1 + '.json', 'w') as f2:
            json.dump(no_list, f2)
        print("Save over")
        continue
    if s.lower() == "load":
        if os.path.exists('train_list' + auto_date_1 + '.json') and os.path.exists('no_list' + auto_date_1 + '.json'):
            with open('train_list' + auto_date_1 + '.json', 'r') as f1:
                train_list = json.load(f1)
            with open('no_list' + auto_date_1 + '.json', 'r') as f2:
                no_list = json.load(f2)
            print("Load over")
        else:
            print("File not exist, load fail")
        continue
    if s.lower() == "city_station":
        while True:
            new = input("City name: ")
            if new == "save" or new == "exit":
                break
            station_name = ""
            city_station[new] = []
            n = input("Station name: ")
            while n != "0" and n.lower() != "end":
                city_station[new].append(n)
                n = input("Station name: ")
        with open('city_station.json', 'w') as f1:
            json.dump(city_station, f1)
        print("City stations data save over")
        continue
    if s.lower() == "time" or s.lower() == "date":
        print("Current date setting:" ,auto_date)
        auto_date = input("Input time setting (xxxx-xx-xx) : ")
        auto_date_1 = auto_date.replace("-", "")
        continue
    if s.lower() == "agent":
        print("Current simulated user-agent:", headers["User-Agent"])
        headers["User-Agent"] = input("Input user-agent setting: ")
        continue
    if s.lower() == "sum":
        count_code()
        continue
    if trace_code > 1 and (s == "<<" or s == "《《"):
        trace_code -= 1
        s = trace[trace_code-1]
    elif trace_code < trace_max and (s == ">>" or s =="》》"):
        trace_code += 1
        s = trace[trace_code-1]
    elif s == "<<" or s == "《《":
        print("Cannot move backward")
        continue
    elif s == ">>" or s =="》》":
        print("Cannot move forward")
        continue
    else:
        trace[trace_code] = s
        trace_code += 1
        trace_max = trace_code
    r = "GDCKTZSYP"
    if "*" in s:
        s, pre = s.split("*")
        r = pre.upper()
    if s[0:4].lower() == "code" or s[0] == '.':
        if s[0:4].lower() == "code":
            target = s[5:].upper()
        else:
            target = s[1:].upper()
        if target in no_list:
            callback = print_train(train_list[no_list[target]])
        else:
            print("Not found")
        continue
    if s[0:7].lower() == "station" or s[-1:] == "站" or s.find("+") > 1 and s[s.find("+")-1] == "站":
        if s[0:7].lower() == "station":
            target = s[8:]
        elif "+" in s:
            target = s[:s.find("+")-1]
        else:
            target = s[:-1]
        if "+" in s:
            s, sort_order =s.split("+")
            callback = search_station(target, sort_order = sort_order, prefix = r)
        else:
            callback = search_station(target, prefix = r)
        continue
    if "--" in s:
        if s.count('-') > 2:
            trace_code -= 1
            print("Instruction grammar error")
            continue
        st, ed = s.split("--")
        add = ""
        if "+" in ed:
            ed, add = ed.split("+")
        s = ""
        if st in city_station:
            for sta in city_station[st]:
                s = s + "/" + sta
            s = s[1:]
        else:
            s = st
        s = s + "-"
        if ed in city_station:
            for sta in city_station[ed]:
                s = s + sta + "/"
            s = s[0:-1]
        else:
            s = s + ed
        if add != "":
            s = s + "+" + add
    if "-" in s:
        if s.count('-') > 1:
            trace_code -= 1
            print("Instruction grammar error")
            continue
        st, ed = s.split("-")
        if "+" in ed:
            if ed.count('+') > 1:
                trace_code -= 1
                print("Instruction grammar error")
                continue
            ed, sort_order = ed.split("+")
            sts = st.split("/")
            eds = ed.split("/")
            callback = search_link(sts, eds, sort_order = sort_order.lower(), prefix = r)
        else:
            sts = st.split("/")
            eds = ed.split("/")
            callback = search_link(sts, eds, prefix = r)
        callback["//"] = st + "-" + ed
        callback["/st"] = st + "-" + ed + "+st" + "*" + r
        callback["/ed"] = st + "-" + ed + "+ed" + "*" + r
        callback["/v"] = st + "-" + ed + "+v" + "*" + r
        continue
    trace_code -= 1
    if trace_max == trace_code + 1:
        trace_max - 1
    print("No suitable instruction")