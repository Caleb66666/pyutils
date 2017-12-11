# -*- coding: utf-8 -*-


# import datetime
import time


def cur_time_str():
    # return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


def cur_time_stamp(ms=False):
    if ms:
        return int(round(time.time() * 1000))
    return int(time.time())


def cur_day():
    return time.strftime("%Y-%m-%d", time.localtime(time.time()))


def time_ts2str(time_ts):
    time_ts = float(time_ts)
    if time_ts > 10 ** 12:
        time_ts = int(time_ts / 1000.0)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_ts))


def time_str2ts(time_str, ms=False):
    time_arr = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    if ms:
        return str(int(time.mktime(time_arr)) * 1000)
    return str(int(time.mktime(time_arr)))

if __name__ == '__main__':
    test_str = "2017-12-11 14:47:55"
    print time_str2ts(test_str)
