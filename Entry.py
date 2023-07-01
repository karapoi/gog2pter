import shutil
import os
from torf import Torrent
import zipfile
import rarfile
import re
import utils

class Entry:
    def __init__(self, logger, conf, gtable, path):
        self.logger = logger
        self.conf = conf
        self.gtable = gtable

        self.path = path  # 在数据文件夹中的名字
        self.origin_path = os.path.join(conf.data_dir, path) # 相对当前目录的路径（或绝对路径）
        self.origin_abs_path = os.path.abspath(self.origin_path) # 绝对路径

        self.transfer_dirname = '' # 转移后的名字
        self.transfer_path = '' # 转移后的路径（或绝对路径）
        self.transfer_abs_path = '' # 转移或解压后的绝对路径
        self.transfer_dir = '' # 转移目录

        self.is_file = False # 是否是单文件
        self.is_compress = False # 是否是单个压缩文件
        self.is_dir = False # 
        
        self.compress_format = '' # 压缩文件的格式，目前支持rar和zip
        self.decompress_dirname = '' # 解压目标文件夹的名字

        self.single_exe = True # 是否只有单个exe文件
        self.exe_file = '' # 主exe安装文件的路径
        self.has_goodies = False # 是否包括goodies
        self.goodies_dirname = '' # goodies文件夹的名字
        self.goodies_path = '' # goodies文件夹的路径
        self.goodies = []

        self.renamed_dirname = '' # 重命名后的名字
        self.renamed_path = '' # 重命名后的路径
        self.renamed_abs_path = '' # 重命名后的绝对路径
        self.renamed_dir = '' # 重命名后所在的文件夹
        
        self.game = '' # 游戏的名字（链接版）
        self.game_info = {} # 游戏的各类信息

        self.torrent = {} # torrent文件

        self.status = 'initial'
        self.info = ''

    # 将压缩文件从原路径解压到转移目录下的同名文件夹中
    def _decompress(self):
        if re.match(r'.*\.zip$', self.origin_path):
            self.compress_format = 'zip'
            f = zipfile.ZipFile(self.origin_path)
        elif re.match(r'.*\.rar$', self.origin_path):
            self.compress_format = 'rar'
            f = rarfile.RarFile(self.origin_path)
        os.mkdir(self.transfer_path)
        f.extractall(path=self.transfer_path)
        dirs = os.listdir(self.transfer_path)
        if len(dirs) == 1:
            if os.path.isdir(os.path.join(self.transfer_path, dirs[0])):
                random_name = 'fjskljcsofnjgas'
                os.rename(os.path.join(self.transfer_path, dirs[0]), os.path.join(self.transfer_dir, random_name))
                os.rmdir(self.transfer_path)
                os.rename(os.path.join(self.transfer_dir, random_name), self.transfer_path)
        f.close()
    
    def _test_compressed(self, path):
        if zipfile.is_zipfile(path):
            print('检查文件' + path)
            with zipfile.ZipFile(path, 'r') as zf:
                if zf.testzip():
                    print('文件' + path + '已损坏')
                    return False
        elif rarfile.is_rarfile(path):
            with rarfile.RarFile(path, 'r') as rf:
                if rf.testrar():
                    print('文件' + path + '已损坏')
                    return False
        else:
            print('文件' + path + '已损坏')
            return False
    
    def ignore(self):
        self.conf.add_ignored_entry(self.path)
        if not self.conf.upload_dir_on:
            if self.is_compress:
                self.conf.add_ignored_entry(self.decompress_dirname)
            self.conf.add_ignored_entry(self.renamed_dirname)
            if self.has_goodies:
                self.conf.add_ignored_entry(self.goodies_dirname)

    def complete(self):
        self.conf.add_completed_entry(self.path)
        if not self.conf.upload_dir_on:
            if self.is_compress:
                self.conf.add_completed_entry(self.decompress_dirname)
            self.conf.add_completed_entry(self.renamed_dirname)
            if self.has_goodies:
                self.conf.add_completed_entry(self.goodies_dirname)

    def transfer(self):
        # 如果启用了上传目录
        if self.conf.upload_dir_on:
            self.transfer_dirname = self.path
            self.transfer_dir = self.conf.upload_dir # 转移目录为上传目录
            self.transfer_path = os.path.join(self.conf.upload_dir, self.path)  # 转移到转移目录下的同名文件夹
            self.transfer_abs_path = os.path.abspath(self.transfer_path)
            
            # 如果转移目录下的已存在同名文件夹则报错并忽略该项
            if os.path.exists(self.transfer_path):
                self.status = 'ignored'
                self.info = self.transfer_path + '已存在于上传目录中，忽略该项'
                self.logger.error(self.info)
                self.ignore()
                return False

            # 如果是单文件
            if os.path.isfile(self.origin_path):
                # 如果是单压缩文件
                if re.match(r'.*\.(rar|zip)$', self.path):
                    self.is_compress = True
                    self.decompress_dirname = re.sub(r'\.(rar|zip)$', '', self.path)
                    self.transfer_dirname = self.decompress_dirname
                    self.transfer_path = os.path.join(self.conf.upload_dir, self.decompress_dirname)
                    self.transfer_abs_path = os.path.abspath(self.transfer_path)
                    # 如果转移目录下的已存在同名文件夹则报错并忽略该项
                    if os.path.exists(self.transfer_path):
                        self.status = 'ignored'
                        self.info = self.transfer_path + '已存在于上传目录中，忽略该项'
                        self.logger.error(self.info)
                        self.ignore()
                        return False
                    self._decompress()
                    self.status = 'transferred'
                    self.logger.info('成功解压文件到上传目录：' + self.transfer_path)
                    return True
                # 如果是单exe文件，则硬链接或者复制到转移目录
                elif re.match(r'setup_.*\.exe$', self.origin_path):
                    if self.conf.hlink_on:
                        os.link(self.origin_path, self.transfer_path)
                    else:
                        shutil.copyfile(self.origin_path, self.transfer_path)
                # 如果是其他格式的单文件则忽略
                else:
                    self.status = 'ignored'
                    self.info = self.origin_path + '为单文件且不是安装文件，忽略该项'
                    self.logger.error(self.info)
                    self.ignore()
                    return False
            # 如果是目录
            else:
                # 如果启用了硬链接迁移
                if self.conf.hlink_on:
                    # 依次创建转移目录下的同名文件夹和子文件夹，并将文件硬链接到相应位置
                    os.mkdir(self.transfer_path)
                    for root, dirs, files in os.walk(self.origin_path):
                        relpath = os.path.relpath(root, self.conf.data_dir)
                        for dir_name in dirs:
                            os.mkdir(os.path.join(self.conf.upload_dir, relpath, dir_name))
                        for file_name in files:
                            os.link(os.path.join(self.conf.data_dir, relpath, file_name), os.path.join(self.conf.upload_dir, relpath, file_name))
                    self.status = 'transferred'
                    self.logger.info('成功链接文件夹到上传目录：' + self.transfer_path)
                    return True
                # 未启用硬链接则直接复制整个文件夹到相应位置
                else:
                    shutil.copytree(self.origin_path, self.transfer_path)
                    self.status = 'transferred'
                    self.logger.info('成功复制文件夹到上传目录：' + self.transfer_path)
                    return True
        # 未启用上传目录则直接在数据目录处理压缩文件
        elif re.match(r'.*\.(rar|zip)$', self.origin_path):
            self.transfer_dir = self.conf.data_dir
            self.decompress_dirname = re.sub(r'\.(rar|zip)$', '', self.path)
            self.transfer_dirname = self.decompress_dirname
            self.transfer_path = os.path.join(self.conf.data_dir, self.decompress_dirname)
            self.transfer_abs_path = os.path.abspath(self.transfer_path)
            # 如果数据目录下的已存在同名文件夹则报错并忽略该项
            if os.path.exists(self.transfer_path):
                self.status = 'ignored'
                self.info = self.transfer_path + '已存在于上传目录中，忽略该项'
                self.logger.error(self.info)
                self.ignore()
                return False
            self._decompress()
            self.status = 'transferred'
            self.logger.info('成功解压文件到数据目录：' + self.transfer_path)
            return True
        # 未启用上传目录且非压缩文件则不处理
        else:
            self.transfer_dir = self.conf.data_dir
            self.transfer_dirname = self.path
            self.transfer_path = self.origin_path
            self.transfer_abs_path = self.origin_abs_path
            self.status = 'transferred'
            self.logger.info('未启用上传目录且不需要解压：' + self.origin_path)
            return True

    def preprocess(self):
        self.goodies_dirname = self.transfer_dirname  + '_goodies'
        self.goodies_path = self.transfer_path + '_goodies'
        self.goodies_abs_path = os.path.abspath(self.goodies_path)
        # 遍历所有子文件夹和文件
        for root, dirs, files in os.walk(self.transfer_path):
            # 如果有子文件夹则不是单exe文件
            if len(dirs):
                self.single_exe = False
            for filename in files:
                if not self.game:
                    crc_value = utils.crc(os.path.join(root, filename))
                    self.game = self.gtable.search(crc_value)
                    if self.game:
                        self.logger.info('成功匹配文件crc，获得游戏名：' + self.game)
                # 移除txt和torrent文件
                if re.match('.*\.(txt|torrent)$', filename):
                    os.remove(os.path.join(root, filename))
                    self.logger.debug('移除txt/torrent文件：' + os.path.join(root, filename))
                # 有压缩包则认为存在goodies，单独建立文件夹
                elif re.match('.*\.(zip|rar)$', filename):
                    if not self.has_goodies:
                        self.has_goodies = True
                        utils.check_dir(self.goodies_path)
                    os.rename(os.path.join(root, filename), os.path.join(self.goodies_path, filename))
                    self.logger.debug(f'移动文件{os.path.join(root, filename)}到{os.path.join(self.goodies_path, filename)}')
                    if re.findall('artbook', filename, re.I):
                        if not 'Artbook' in self.goodies:
                            self.goodies.append('Artbook')
                    elif re.findall('ost|soundtrack', filename, re.I):
                        if not 'Soundtrack' in self.goodies:
                            self.goodies.append('Soundtrack')
                    elif re.findall('manual|handbuch|reference', filename, re.I):
                        if not 'Guides' in self.goodies:
                            self.goodies.append('Guides')
                    if self.conf.check_compressed and not self._test_compressed(os.path.join(self.goodies_path, filename)):
                        self.status = 'ignored'
                        self.info = '压缩文件' + os.path.join(self.goodies_path, filename) + '已损坏，程序中止...'
                        self.logger.error(self.info)
                        self.ignore()
                        return False
                # 如果文件为exe文件
                elif re.match('.*\.exe$', filename):
                    self.logger.debug('发现exe文件' + os.path.join(root, filename))
                    # 如果已发现其他exe文件则说明不是单exe文件的情况
                    if self.exe_file:
                        self.single_exe = False
                    # 如果是exe安装文件，就记录其路径并提取文件夹的正确命名
                    if re.match('setup_.*', filename):
                        self.logger.debug('发现安装文件：' + os.path.join(root, filename))
                        # 为单exe文件的情况下，各个路径如下
                        self.renamed_dir = root
                        self.renamed_dirname = filename
                        self.renamed_path = os.path.join(root, filename)
                        self.renamed_abs_path = os.path.abspath(self.renamed_path)
                        # 主安装文件一般没有修饰词，名字比较短
                        if (not self.exe_file) or len(filename) <= len(self.exe_file):
                            self.exe_file = filename
                    else:
                        self.logger.debug('发现未知的exe文件：' + os.path.join(root, filename))
                        self.single_exe = False
                else:
                    self.logger.debug('发现未知格式文件：' + os.path.join(root, filename))
                    self.single_exe = False

        # 如果没有发现exe安装文件，则报错退出, 并忽略该项
        if not self.exe_file:
            self.status = 'ignored'
            self.info = self.transfer_path + '未检测到安装文件，程序中止...'
            self.logger.error(self.info)
            self.ignore()
            return False
        # 从主exe安装文件名获取游戏名
        exe_file_body = re.sub(r'(^setup_)|(\.exe$)', '', self.exe_file)
        if not self.game:
            self.game = re.sub(r'((_\(\d+\))|(_(\d+\.)+\d+)|(_windows)|(_gog)|(_pro)|(_\(64bit\)))', '', exe_file_body)
            guessed_game = self.gtable.guess(self.game)
            if guessed_game:
                self.game = guessed_game
            else:
                self.game = re.sub('_\-', '', self.game)
        # 如果是单exe安装文件
        if self.single_exe:
            self.status = 'preprocessed'
            self.logger.info('预处理得到单exe安装文件：' + self.renamed_path)
            return True
        # 如果不是单exe安装文件
        else:
            self.renamed_dir = self.transfer_dir
            exe_file_body = re.sub(r'(^setup_)|(\.exe$)', '', self.exe_file)
            self.renamed_dirname = exe_file_body + '-GOG'
            self.renamed_path = os.path.join(self.renamed_dir, self.renamed_dirname)
            self.renamed_abs_path = os.path.abspath(self.renamed_path)
            # 如果当前文件名不是主exe安装文件名中提取的文件夹名
            if not os.path.normcase(self.transfer_path) == os.path.normcase(self.renamed_path):
                # 重命名
                if not os.path.exists(self.renamed_path):
                    os.rename(self.transfer_path, self.renamed_path)
                    self.logger.debug(f'重命名文件夹{self.transfer_path}为{self.renamed_path}')
                # 如果已存在该名字的文件夹，则全部忽略
                else:
                    self.status = 'ignored'
                    self.info = self.renamed_path + '已存在于上传目录中，忽略该项'
                    self.logger.error(self.info)
                    self.ignore()
                    return False
                self.logger.info('预处理得到文件夹：' + self.renamed_path)
                
                # 重命名Goodies
                if self.has_goodies:
                    cur_goodies_path = self.goodies_path
                    self.goodies_dirname = self.renamed_dirname  + '_goodies'
                    self.goodies_path = self.renamed_path + '_goodies'
                    self.goodies_abs_path = os.path.abspath(self.goodies_path)
                    if not os.path.exists(self.goodies_path):
                        os.rename(cur_goodies_path, self.goodies_path)
                        self.logger.debug(f'重命名文件夹{cur_goodies_path}为{self.goodies_path}')
                    # 如果已存在该名字的文件夹，则全部忽略
                    else:
                        self.status = 'ignored'
                        self.info = self.goodies_path + '已存在于上传目录中，忽略该项'
                        self.logger.error(self.info)
                        self.ignore()
                        return False
                    self.logger.info('预处理得到文件夹：' + self.goodies_path)
            # 如果当前文件名与提取的文件夹名一致，不操作
            else:
                self.logger.debug(f'文件夹{self.transfer_path}无需重命名')
                self.logger.info('预处理得到文件夹：' + self.renamed_path)
            self.status = 'preprocessed'
            return True

    def make_torrent(self):
        # 对主体做种
        self.torrent['main'] = os.path.join(self.conf.torrent_dir, '[PTer]' + self.game + '.torrent')
        t = Torrent(path=self.renamed_path, trackers=[self.conf.announce], comment=self.conf.comment)
        t.private = True
        t.metainfo['info']['source'] = '[pterclub.com] ＰＴ之友俱乐部'
        t.generate()
        if os.path.exists(self.torrent['main']):
            os.remove(self.torrent['main'])
        t.write(self.torrent['main'])
        del t
        self.logger.info('种子已生成：' + self.torrent['main'])
        # 对goodies做种
        if self.has_goodies:
            self.torrent['goodies'] = os.path.join(self.conf.torrent_dir, '[PTer]' + self.game + '_goodies.torrent')
            tg = Torrent(path=self.goodies_path, trackers=[self.conf.announce], comment='')
            tg.private = True
            tg.metainfo['info']['source'] = '[pterclub.com] ＰＴ之友俱乐部'
            tg.generate()
            if os.path.exists(self.torrent['goodies']):
                os.remove(self.torrent['goodies'])
            tg.write(self.torrent['goodies'])
            del tg
            self.logger.info('种子已生成：' + self.torrent['goodies'])
        self.status = 'torrent_maked'
