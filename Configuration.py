# bug: a tale of paper: refold
# bug: cookie导入但未能登录
import configparser
import csv
import datetime
from time import strftime
import json

class Configuration:
    def __init__(self):
        self.get_config()

        self.ignored_entries = []
        self.completed_entries = []
        
        self.records_file = 'log/records.csv'
        self.records = []

    def get_config(self):
        with open('config/cookies.json', 'r') as r:
            self.cookies = json.load(r)
            self.pter_cookies = self.cookies['pter']
            self.pic_cookies = self.cookies['pic']

        config = configparser.ConfigParser()
        config.read('config/config.ini')
        self.upload_dir_on = (config['MODE']['upload_dir_on'] == 'True')
        self.hlink_on = (config['MODE']['hlink_on'] == 'True')
        self.proxies = config['MODE']['proxies']
        self.use_pic_host = (config['MODE']['use_pic_host'] == 'True')
        self.check_compressed = (config['MODE']['check_compressed'] == 'True')
        self.comment = config['MODE']['comment']
        self.passkey = config['PTER']['passkey']
        self.announce = 'https://tracker.pterclub.com:443/announce?passkey=' + self.passkey
        self.anonymous = 'yes' if config['PTER']['anonymous'] == 'True' else 'no'
        self.torrent_dir = config['WORKDIR']['torrent_dir']
        self.data_dir = config['WORKDIR']['data_dir']
        self.upload_dir = config['WORKDIR']['upload_dir']
        self.seed = (config['MODE']['seed'] == 'True')
        self.client_type = config['CLIENT']['type']
        self.client_ip = config['CLIENT']['ip']
        self.client_port = config['CLIENT']['port']
        self.client_username = config['CLIENT']['username']
        self.client_password = config['CLIENT']['password']
        self.save_path = config['CLIENT']['save_path']

    def add_ignored_entry(self, entry_path):
        if entry_path:
            if not entry_path in self.ignored_entries:
                self.ignored_entries.append(entry_path)

    def remove_ignored_entry(self, entry_path):
        if entry_path:
            if entry_path in self.ignored_entries:
                self.ignored_entries.remove(entry_path)
        
    def add_completed_entry(self, entry_path):
        if entry_path:
            if not entry_path in self.completed_entries:
                self.completed_entries.append(entry_path)
        
    def remove_completed_entry(self, entry_path):
        if entry_path:
            if entry_path in self.completed_entries:
                self.completed_entries.remove(entry_path)

    def add_record(self, entry):
        header = ['时间', '条目', '结果', '备注信息']
        data = [{'时间':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '条目':entry.path, '结果':entry.status, '备注信息':entry.info}]
        self.records.append(data)
        with open(self.records_file, mode='a', encoding='utf-8-sig', newline='') as record_f:
            writer = csv.DictWriter(record_f, header)
            writer.writerows(data)
