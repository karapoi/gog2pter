import re
import os
import logging
import csv
import zlib

def check_yes(str, default=False):
    ans = input(str).lower()
    if ans in ['y', 'yes']:
        return True
    elif ans in ['n', 'no']:
        return False
    else:
        return default

def true_input(content):
    while True:
        output = input(content)
        if output == '':
            print('输入内容不能为空！')
        else:
            return output

def check_dir(str):
    path = os.path.expanduser(str)
    if not os.path.exists(path):
        os.mkdir(path)
    elif os.path.isfile(path):
        logging.critical(str + '是一个文件而非目录，程序中止...')
        raise Exception()
    elif not os.access(path, os.R_OK):
        logging.critical(str + '目录不可读，程序中止...')
        raise Exception()
    elif not os.access(path, os.W_OK):
        logging.critical(str + '目录不可写，程序中止...')
        raise Exception()

def check_file(str):
    path = os.path.expanduser(str)
    if not os.path.exists(path):
        f = open(path, 'w')
        if not f:
            logging.critical('创建文件' + str + '失败，程序中止...')
            raise Exception()
        else:
            f.close()
    elif not os.path.isfile(path):
        logging.critical(str + '不是一个文件，程序中止...')
        raise Exception()
    elif not os.access(path, os.R_OK):
        logging.critical(str + '文件不可读，程序中止...')
        raise Exception()
    elif not os.access(path, os.W_OK):
        logging.critical(str + '文件不可写，程序中止...')
        raise Exception()

def init_log():
    check_dir('log')
    check_file('log/log.txt')
    header = ['时间', '条目', '结果', '备注信息']
    if not os.path.exists('log/records.csv'):
        with open('log/records.csv', mode='w', encoding='utf-8-sig', newline='') as record_file:
            writer = csv.DictWriter(record_file, header)
            writer.writeheader()

    logger = logging.getLogger('default')
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    log_file = logging.FileHandler('log/log.txt', 'a', encoding='utf-8')
    log_file.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - line:%(lineno)d - %(levelname)s - %(message)s')
    log_file.setFormatter(formatter)
    
    logger.addHandler(log_file)
    return logger

def crc(filename):
    prev = 0
    for eachLine in open(filename,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X"%(prev & 0xFFFFFFFF)