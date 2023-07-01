import requests
import re
from bs4 import BeautifulSoup
import json
import time
import random

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache', }
                
PTER_DOMAIN = 'https://pterclub.com/'

class PTerApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = HEADERS
        with open('config/cookies.json', 'r') as r:
            self.cookies = json.load(r)
            self.cookies = self.cookies['pter']
        self._install_cookies()

    # 加载cookie到session
    def _install_cookies(self):
        self.session.headers.update({'Referer': PTER_DOMAIN})
        cookies = dict([field.split('=', 1) for field in self.cookies.split('; ')])
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)

    def find_game(self, name):
        # 搜索游戏
        url = PTER_DOMAIN + 'searchgameinfo.php'
        data = {'name': name}
        res = self.session.post(url, data=data)
        res_soup = BeautifulSoup(res.text, 'lxml')
        game_list = res_soup.select('a[title="点击发布这游戏设备的种子"]')
        platform_list = res_soup.select('img[src^="/pic/category/chd/scenetorrents/"]')
        if not game_list:
            return False
        else:
            return True
        #game_dict = {}
        #num = 1
        ## 获取游戏列表
        #for game, platform in zip(game_list[::2], platform_list):
        #    gid = re.search(r'detailsgameinfo.php\?id=(\d+)', game['href']).group(1)
        #    game_dict[str(num)] = '{}: {} GID:{}'.format(platform['title'], game.text, gid)
        #    num += 1
        ## 选择上传的目标游戏
        #print('我们在猫站找到以下游戏：')
        #for num, game in game_dict.items():
        #    print('{}.{}'.format(num, game))

def main():
    games = []
    with open('gog-games/gog_collection.sfv') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                file_hash = re.split('\s+', line)
                if len(file_hash) == 2:
                    file = file_hash[0]
                    crc = file_hash[1]
                    game_filename = file.split('/', 1)
                    if len(game_filename) == 2:
                        game = game_filename[0]
                        if len(game) > 4:
                            game = game.replace('_', ' ')
                            if not game in games:
                                games.append(game)
    pter = PTerApi()
    print('正在查找尚未发布的游戏...')
    start = random.randint(1, len(games))
    for i in range(start, len(games)):
        game = games[i]
        time.sleep(3)
        if pter.find_game(game):
            continue
        else:
            print('发现以下游戏可能尚未发布：' + game)
            if input('是否继续，继续直接回车：'):
                break


if __name__ == '__main__':
    main()