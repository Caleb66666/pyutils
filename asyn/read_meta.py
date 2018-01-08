# -*- coding: utf-8 -*-


def gen_meta_dict(meta_lines):
    meta_dict = dict()
    for line in meta_lines:
        key, value = line.split("\t")
        meta_dict.update({key.strip(): value.strip()})

    return meta_dict


def read_meta(meta_path):
    meta_dict_list = list()
    one_meta = list()
    with open(meta_path, "r") as fd:
        for line in fd.readlines():
            if len(line) <= 1:
                if len(one_meta) > 0:
                    meta_dict_list.append(gen_meta_dict(one_meta))
                    one_meta[:] = []
            else:
                one_meta.append(line)

    return meta_dict_list


if __name__ == '__main__':
    meta_path = "meta/meta1-5"
    meta_data = read_meta(meta_path)

    for item in meta_data:
        print "=========================="
        for key, value in item.items():
            print key, value
        print "=========================="
