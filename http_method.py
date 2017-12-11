# -*- coding: utf-8 -*-

from chardet import detect
import urlparse
import requests


def is_encoding(content, encoding):
    """
    检查encoding编码方式是否适合content内容
    :param content:
    :param encoding:
    :return:
    """
    try:
        diff = content.decode(encoding, "ignore").encode(encoding)
        sizes = len(diff), len(content)
        if abs(len(content) - len(diff)) < max(sizes) * 0.01:
            return True, "correct encoding"
        else:
            return False, "err encoding: huge diff"
    except Exception as e:
        return False, "err encoding: %s" % str(e)


def encode_detect(byte_str):
    """
    使用chardet检查获取网页内容的编码，如果获取编码的成功率小于0.7，则分别使用"gb18030"或者"utf-8"作为编码方式
    :param byte_str:
    :return:
    """

    try:
        detect_result = detect(byte_str)
        if detect_result.get("confidence") < 0.7:
            gbk_ret = is_encoding(byte_str, "gb18030")
            if gbk_ret[0]:
                encoding = "gb18030"
            else:
                encoding = "utf-8"
        else:
            encoding = detect_result.get("encoding").lower()

        if encoding in ("gbk", "gb2312"):
            encoding = "gb18030"
        return True, encoding
    except Exception as e:
        return False, "encode detect failed: %s" % str(e)


def fetch_referer(url):
    parse_result = urlparse.urlparse(url)
    if parse_result.path in ('', '/'):
        return "https://www.baidu.com/"
    return "%s://%s/" % (parse_result.scheme, parse_result.netloc)


def http_fetch(url, user_agent, method="GET", params=None, referer=None, proxies=None, cookies=None, timeout=7):
    kwargs = {"url": url, "timeout": timeout}

    headers = {
        "User-Agent": user_agent
    }
    if referer:
        headers.update({"Referer": referer})
    kwargs.update({"headers": headers})

    if proxies:
        kwargs.update({"proxies": proxies})

    if cookies:
        kwargs.update({"cookies": cookies})

    method = method.upper()
    if method == "GET":
        kwargs.update({"params": params})
        try:
            ret = requests.get(**kwargs)
        except Exception as e:
            return False, "http failed: %s" % str(e)
    else:
        kwargs.update({"data": params})
        try:
            ret = requests.post(**kwargs)
        except Exception as e:
            return False, "http failed: %s" % str(e)

    if ret.status_code != requests.codes.ok:
        return False, "http failed: status %s" % ret.status_code

    detect_ret = encode_detect(ret.content)
    if not detect_ret[0]:
        return detect_ret
    ret.encoding = detect_ret[1]
    return True, ret.text
