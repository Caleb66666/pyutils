# -*- coding: utf-8 -*-

from gevent import monkey

monkey.patch_all()
from gevent.queue import Queue
from handler import HandlerManager
import requests
from lxml import html
from urlparse import urljoin
from time import sleep


class WorkFlow(object):
    def __init__(self, page_base, start_index, end_index):
        self.page_task = Queue()
        self.page_success = Queue()

        self.article_info = Queue()
        self.detail_success = Queue()

        self.page_base = page_base
        self.start = start_index
        self.end = end_index
        self.path = "./meta/meta%s-%s" % (start_index, end_index)

    @staticmethod
    def page_asyn(task):
        url = task
        try:
            resp = requests.get(url=url, timeout=5)
        except Exception as e:
            return False, "http failed: %s" % str(e)
        if resp.status_code != requests.codes.ok:
            return False, "http status code: %s" % resp.status_code
        return True, resp.content

    @staticmethod
    def page_callback(asyn_ret, task, task_queue, success_queue):
        if not asyn_ret[0]:
            print "failed: %s" % asyn_ret[1]
            task_queue.put(task)
            return

        etree = html.fromstring(asyn_ret[1])
        target_nodes = etree.xpath("//div[@class='savelist_box']")
        for node in target_nodes:
            app_url = node.xpath("div[1]/div[1]/span[1]/@appurl")[0]
            article_type = node.xpath("ul[1]/li[1]/a[1]/text()")[0].strip()[1:-1]
            success_queue.put((app_url, 4, article_type))

    def fetch_details(self):
        # 生成所有列表页的链接
        for i in xrange(self.start, self.end + 1):
            self.page_task.put("%s%s" % (self.page_base, i))

        # 构建协程参数，并运行
        handler_args = {
            "asyn_work": self.page_asyn,
            "callback": self.page_callback
        }
        gr_group = HandlerManager(task_queue=self.page_task, concurrency=3,
                                  success_queue=self.page_success, handler_args=handler_args)
        gr_group.run()

    def run(self):
        self.fetch_details()
        print "fetch all urls of articles successfully, and sizes: %s" % self.page_success.qsize()
        self.fetch_articles()
        print "get all meta data of articles successfully!"

    @staticmethod
    def detail_asyn(task):
        url, try_times, article_type = task
        try:
            resp = requests.get(url=url, timeout=5)
        except Exception as e:
            return False, "http failed: %s" % str(e)
        if resp.status_code != requests.codes.ok:
            return False, "http status code: %s" % resp.status_code
        return True, resp.content

    def parse_article_info(self, asyn_ret, task):
        etree = html.fromstring(asyn_ret[1])
        total_info = list()

        # 题名
        article_name = etree.xpath("//h4[@class='falv_tit']/text()")[0].strip()
        total_info.append({"题名": article_name})

        # 包含所有信息的总标签
        target_nodes = etree.xpath("//ul[@class='infolist']")
        if len(target_nodes) <= 0:
            print "task: %s has no infolist..." % task[0]
            return total_info
        target_node = target_nodes[0]

        # 获取途径
        fetch_ways = target_node.xpath("li[1]/a")
        if len(fetch_ways) <= 0:
            total_info.append({"获取途径": "该文献暂无获取途径"})
        else:
            ways = list()
            for fetch_way in fetch_ways:
                way_name = fetch_way.xpath('text()')[0].encode("utf-8")
                way_url = urljoin(self.page_base, fetch_way.xpath('@href')[0])
                ways.append("%s(%s)" % (way_name, way_url))
            total_info.append({"获取途径": ",".join(ways)})

        # 用于表示不同的li标签，只有检测到有，才能加一递推
        li_pointer = 2

        ##########
        # 类型为期刊独有的元数据
        ##########
        if task[2] == u"期刊":
            # 英文题名
            eng_name_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "英文题名" in eng_name_header.encode("utf-8"):
                eng_name = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(eng_name) <= 0:
                    total_info.append({"英文题名": "无"})
                else:
                    total_info.append({"英文题名": eng_name[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"英文题名": "无"})

            # 作者
            author_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "作者" in author_header.encode("utf-8"):
                authors = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(authors) <= 0:
                    total_info.append({"作者": "无"})
                else:
                    total_info.append({"作者": ",".join(authors)})
                li_pointer += 1
            else:
                total_info.append({"作者": "无"})

            # 英文作者
            english_author_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "英文作者" in english_author_header.encode("utf-8"):
                english_authors = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(english_authors) > 0:
                    total_info.append({"英文作者": english_authors[0].encode("utf-8")})
                else:
                    total_info.append({"英文作者": "无"})
                li_pointer += 1
            else:
                total_info.append({"英文作者": "无"})

            # 期刊名
            journal_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "期刊名" in journal_header.encode("utf-8"):
                journal = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(journal) <= 0:
                    total_info.append({"期刊名": "无"})
                else:
                    total_info.append({"期刊名": journal[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"期刊名": "无"})

            # 英文期刊名
            eng_journal_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "英文期刊名" in eng_journal_header.encode("utf-8"):
                eng_journal = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(eng_journal) <= 0:
                    total_info.append({"英文期刊名": "无"})
                else:
                    total_info.append({"英文期刊名": eng_journal[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"英文期刊名": "无"})

            # 作者单位
            org_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "作者单位" in org_header.encode("utf-8"):
                org_names = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(org_names) <= 0:
                    total_info.append({"作者单位": "无"})
                else:
                    new_org_names = list()
                    for name in org_names:
                        new_org_names.append(name.encode("utf-8").strip())
                    total_info.append({"作者单位": ",".join(new_org_names)})
                li_pointer += 1
            else:
                total_info.append({"作者单位": "无"})

            # 年份
            year_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "年份" in year_header.encode("utf-8"):
                year = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(year) <= 0:
                    total_info.append({"年份": "无"})
                else:
                    total_info.append({"年份": year[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"年份": "无"})

            # 卷号
            column_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "卷号" in column_header.encode("utf-8").replace(" ", ""):
                column = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(column) <= 0:
                    total_info.append({"卷号": "无"})
                else:
                    total_info.append({"卷号": column[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"卷号": "无"})

            # 期号
            phase_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "期号" in phase_header.encode("utf-8"):
                phase = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(phase) <= 0:
                    total_info.append({"期号": "无"})
                else:
                    total_info.append({"期号": phase[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"期号": "无"})

            # 页码
            script_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "页码" in script_header.encode("utf-8").replace(" ", ""):
                script = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(script) <= 0:
                    total_info.append({"页码": "无"})
                else:
                    total_info.append({"页码": script[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"页码": "无"})

            # ISSN
            issn_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "ISSN" in issn_header.encode("utf-8"):
                issn = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(issn) <= 0:
                    total_info.append({"ISSN": "无"})
                else:
                    total_info.append({"ISSN": issn[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"ISSN": "无"})

            # 关键词
            key_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "关键词" in key_header.encode("utf-8"):
                keys = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(keys) <= 0:
                    total_info.append({"关键词": "无"})
                else:
                    keys_list = [key.encode("utf-8").strip() for key in keys]
                    total_info.append({"关键词": ",".join(keys_list)})
                li_pointer += 1
            else:
                total_info.append({"关键词": "无"})

            # 英文关键词
            eng_key_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "英文关键词" in eng_key_header.encode("utf-8"):
                eng_keys = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(eng_keys) <= 0:
                    total_info.append({"英文关键词": "无"})
                else:
                    keys_list = [key.encode("utf-8").strip() for key in eng_keys]
                    total_info.append({"英文关键词": ",".join(keys_list)})
                li_pointer += 1
            else:
                total_info.append({"英文关键词": "无"})

            # 分类号
            class_code_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "分类号" in class_code_header.encode("utf-8"):
                class_codes = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(class_codes) <= 0:
                    total_info.append({"分类号": "无"})
                else:
                    total_info.append({"分类号": class_codes[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"分类号": "无"})

            # 摘要有两段，取第一段，但是指针往后移动两步
            abstract_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "摘要" in abstract_header.encode("utf-8"):
                abstract = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(abstract) <= 0:
                    total_info.append({"摘要": "无"})
                else:
                    total_info.append({"摘要": abstract[0].encode("utf-8")})
                li_pointer += 2
            else:
                total_info.append({"摘要": "无"})

            # 基金
            fund_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "基金" in fund_header.encode("utf-8"):
                funds = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(funds) <= 0:
                    total_info.append({"基金": "无"})
                else:
                    total_info.append({"基金": funds[0].encode("utf-8")})
                li_pointer += 1
            else:
                total_info.append({"基金": "无"})

        ##########
        # 类型为图书独有的元数据
        ##########
        if task[2] == u"图书":
            # 英文题名
            eng_name_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "英文题名" in eng_name_header.encode("utf-8"):
                eng_name = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(eng_name) <= 0:
                    total_info.append({"英文题名": "无"})
                else:
                    total_info.append({"英文题名": eng_name[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"英文题名": "无"})

            # 作者
            author_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "作者" in author_header.encode("utf-8"):
                authors = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(authors) <= 0:
                    total_info.append({"作者": "无"})
                else:
                    total_info.append({"作者": ",".join(authors)})
                li_pointer += 1
            else:
                total_info.append({"作者": "无"})

            # 丛书名
            series_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "丛书名" in series_header.encode("utf-8"):
                series = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(series) <= 0:
                    total_info.append({"丛书名": "无"})
                else:
                    total_info.append({"丛书名": ",".join(series)})
                li_pointer += 1
            else:
                total_info.append({"丛书名": "无"})

            # 出版日期
            pubtime_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "出版日期" in pubtime_header.encode("utf-8"):
                pub_time = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(pub_time) <= 0:
                    total_info.append({"出版日期": "无"})
                else:
                    total_info.append({"出版日期": pub_time[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"出版日期": "无"})

            # 出版社
            press_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "出版社" in press_header.encode("utf-8"):
                press = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(press) <= 0:
                    total_info.append({"出版社": "无"})
                else:
                    total_info.append({"出版社": press[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"出版社": "无"})

            # 页码
            script_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "页码" in script_header.encode("utf-8").replace(" ", ""):
                script_num = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(script_num) <= 0:
                    total_info.append({"页码": "无"})
                else:
                    total_info.append({"页码": script_num[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"页码": "无"})

            # ISBN
            isbn_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "ISBN" in isbn_header.encode("utf-8"):
                isbn = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(isbn) <= 0:
                    total_info.append({"ISBN": "无"})
                else:
                    total_info.append({"ISBN": isbn[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"ISBN": "无"})

            # 主题词
            topic_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "主题词" in topic_header.encode("utf-8"):
                topics = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(topics) <= 0:
                    total_info.append({"主题词": "无"})
                else:
                    total_info.append({"主题词": ",".join(topics)})
                li_pointer += 1
            else:
                total_info.append({"主题词": "无"})

            # 中图分类号
            cn_class_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "中图分类号" in cn_class_header.encode("utf-8"):
                cn_class = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(cn_class) <= 0:
                    total_info.append({"中图分类号": "无"})
                else:
                    total_info.append({"中图分类号": cn_class[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"中图分类号": "无"})

            # 摘要
            abstract_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "摘要" in abstract_header.encode("utf-8"):
                abstract = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(abstract) <= 0:
                    total_info.append({"摘要": "无"})
                else:
                    total_info.append({"摘要": abstract[0].strip()})
                li_pointer += 2
            else:
                total_info.append({"摘要": "无"})

        if task[2] == u"学位论文":
            # 作者
            author_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "作者" in author_header.encode("utf-8"):
                authors = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(authors) <= 0:
                    total_info.append({"作者": "无"})
                else:
                    total_info.append({"作者": ",".join(authors)})
                li_pointer += 1
            else:
                total_info.append({"作者": "无"})

            # 学位名称
            degree_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "学位名称" in degree_header.encode("utf-8"):
                degree = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(degree) <= 0:
                    total_info.append({"学位名称": "无"})
                else:
                    total_info.append({"学位名称": ",".join(degree)})
                li_pointer += 1
            else:
                total_info.append({"学位名称": "无"})

            # 外文题名
            foreign_name_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "外文题名" in foreign_name_header.encode("utf-8"):
                foreign_name = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(foreign_name) <= 0:
                    total_info.append({"外文题名": "无"})
                else:
                    total_info.append({"外文题名": foreign_name[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"外文题名": "无"})

            # 学位年度
            degree_year_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "学位年度" in degree_year_header.encode("utf-8"):
                degree_year = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(degree_year) <= 0:
                    total_info.append({"学位年度": "无"})
                else:
                    total_info.append({"学位年度": degree_year[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"学位年度": "无"})

            # 学位授予单位
            degree_org_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "学位授予单位" in degree_org_header.encode("utf-8"):
                degree_org = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(degree_org) <= 0:
                    total_info.append({"学位授予单位": "无"})
                else:
                    total_info.append({"学位授予单位": ",".join(degree_org)})
                li_pointer += 1
            else:
                total_info.append({"学位授予单位": "无"})

            # 导师姓名
            teacher_name_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "导师姓名" in teacher_name_header.encode("utf-8"):
                teacher_name = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(teacher_name) <= 0:
                    total_info.append({"导师姓名": "无"})
                else:
                    total_info.append({"导师姓名": ",".join(teacher_name)})
                li_pointer += 1
            else:
                total_info.append({"导师姓名": "无"})

            # 关键词
            keyword_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "关键词" in keyword_header.encode("utf-8"):
                keyword = target_node.xpath("li[%s]/a/text()" % li_pointer)
                if len(keyword) <= 0:
                    total_info.append({"关键词": "无"})
                else:
                    total_info.append({"关键词": ",".join(keyword)})
                li_pointer += 1
            else:
                total_info.append({"关键词": "无"})

            # 分类号
            class_num_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "分类号" in class_num_header.encode("utf-8"):
                class_num = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(class_num) <= 0:
                    total_info.append({"分类号": "无"})
                else:
                    total_info.append({"分类号": class_num[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"分类号": "无"})

            # 摘要
            abstract_header = target_node.xpath("li[%s]/em/text()" % li_pointer)[0]
            if "摘要" in abstract_header.encode("utf-8"):
                abstract = target_node.xpath("li[%s]/text()" % li_pointer)
                if len(abstract) <= 0:
                    total_info.append({"摘要": "无"})
                else:
                    total_info.append({"摘要": abstract[0].strip()})
                li_pointer += 1
            else:
                total_info.append({"abstract": "无"})

        # 文献类型
        total_info.append({"文献类型": task[2]})

        return total_info

    @staticmethod
    def u2str(byte_str):
        try:
            return byte_str.encode("utf-8")
        except:
            return byte_str

    def detail_callback(self, asyn_ret, task, task_queue, success_queue):
        url, try_times, article_type = task
        if not asyn_ret[0]:
            if try_times <= 0:
                print "url: %s, has tried 4 times, delimit.."
                return
            task_queue.put((url, try_times - 1, article_type))
            return

        parsed_info = self.parse_article_info(asyn_ret, task)
        with open(self.path, "a") as fd:
            for item in parsed_info:
                for key, value in item.items():
                    fd.write("%s\t%s" % (self.u2str(key), self.u2str(value)))
                    fd.write("\n")
            fd.write("\n\n")

    def fetch_articles(self):
        handler_args = {
            "asyn_work": self.detail_asyn,
            "callback": self.detail_callback
        }
        gr_group = HandlerManager(task_queue=self.page_success, concurrency=4,
                                  success_queue=self.detail_success, handler_args=handler_args)
        gr_group.run()


def batch_crawl(page_base, start, end):
    batch_num = (end - start + 1 + 5 - 1) / 5
    # print "batch num: %s" % batch_num
    for i in range(batch_num - 1):
        # print "%s -- %s " % (start + i * 5, start + 4 + i * 5)
        work_flow = WorkFlow(page_base, (start + i * 5), (start + 4 + i * 5))
        work_flow.run()
        sleep(4 * 60)
    work_flow = WorkFlow(page_base, (batch_num - 1) * 5 + start, end)
    # print "%s -- %s" % ((batch_num - 1) * 5 + start, end)
    work_flow.run()


if __name__ == '__main__':
    one_page_base = "http://www.zhizhen.com/s?sw=%E6%97%85%E6%B8%B8%E7%BB%9F%E8%AE%A1&strchannel=11%2C12%2C1%2C2%2C3%2C5&stryear=12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20&size=15&isort=0&x=0_913&pages="
    batch_crawl(one_page_base, 161, 200)
