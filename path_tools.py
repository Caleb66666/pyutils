# -*- coding: utf-8 -*-

import os
import time_tools


def get_cur_path():
    return os.getcwd()


def get_project_root(file_in_root=time_tools):
    return os.path.dirname(file_in_root.__file__)


def recursive_mkdir(dir_path):
    if os.path.isdir(dir_path):
        return
    return os.makedirs(dir_path)


if __name__ == '__main__':
    pass
