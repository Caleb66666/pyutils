# -*- coding: utf-8 -*-

from gevent import monkey, Greenlet, sleep
from gevent.pool import Group
monkey.patch_socket()


class WorkHandler(Greenlet):
    def __init__(self, task_queue, success_queue, asyn_work, callback=None):
        Greenlet.__init__(self)
        self.task_queue = task_queue
        self.success_queue = success_queue
        self.asynchronous_work = asyn_work
        self.callback = callback

        self.start()

    def _run(self):
        while not self.task_queue.empty():
            task = self.task_queue.get()
            work_ret = self.asynchronous_work(task)
            if self.callback:
                self.callback(work_ret, task, self.task_queue, self.success_queue)
            sleep(1)


class HandlerManager(object):
    def __init__(self, task_queue, concurrency, success_queue, handler_args):
        self.task_queue = task_queue
        self.success_queue = success_queue
        self.unit_num = (self.task_queue.qsize() + concurrency - 1) / concurrency
        self.handler_args = handler_args

        self.gr_group = Group()

    def run(self):
        for _ in xrange(self.unit_num):
            g = WorkHandler(self.task_queue, self.success_queue, **self.handler_args)
            self.gr_group.add(g)

        try:
            self.gr_group.join()
        except Exception as e:
            print "gr group err: %s" % str(e)
            return