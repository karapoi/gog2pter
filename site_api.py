import requests
import re
from bs4 import BeautifulSoup
import os
import time
import utils
import datetime
import transmission_rpc
import qbittorrentapi
import demoji

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache', }
PLATFORM_NAME = {'osx':'Mac', 'windows':'Windows', 'linux':'Linux'}
PLATFORM_DICT = {'Switch': '20', 'Game Boy Advance': '24', 'Game Boy': '22', 'Game Boy Color': '22', 'Wii U': '30',
                    'Wii': '30',
                    'Mac': '37', 'iOS': '38',
                    'Windows': '16', 'DOS': '17', 'Xbox': '18', 'Xbox 360': '19',
                    'PlayStation 1': '32', 'PlayStation 2': '33', 'PlayStation 3': '35', 'PlayStation 4': '31',
                    'PlayStation Vita': '36', 'PlayStation Portable': '34',
                    'Android': '45',
                    'Linux': '46'}
LAN_NAME = {    "ar":"阿拉伯语",
                "be":"白俄罗斯语",
                "br":"葡萄牙语（巴西）",
                "cn":"简体中文",
                "cz":"捷克语",
                "de":"德语",
                "en":"英语",
                "es":"西班牙语（西班牙）",
                "es_mx":"西班牙语（拉丁美洲）",
                "fa": "波斯语",
                "fi": "芬兰语",
                "fr":"法语",
                "gk": "希腊语",
                "he": "希伯来语",
                "hu":"匈牙利语",
                "it":"意大利语",
                "jp":"日语",
                "ko":"韩语",
                "nl":"荷兰语",
                "pl":"波兰语",
                "pt": "葡萄牙语",
                "ro": "罗马尼亚语",
                "ru":"俄语",
                "sb": "塞尔维亚语",
                "sv": "瑞典语",
                "th":"泰语",
                "tr":"土耳其语",
                "uk": "乌克兰语",
                "zh":"繁体中文"}
REQ_NAME = {    "system":"系统",
                "processor":"处理器",
                "memory":"内存",
                "graphics":"显卡",
                "network":"网络",
                "directx":"DirectX",
                "storage":"硬盘",
                "sound":"声卡",
                "other":"其他"}
GOODIES_TYPE = {"Artbook": '5', # Artwork
                "Soundtrack": '7', # OST
                "Guides": '6' # Game Guides
                }
                
PTER_DOMAIN = 'https://pterclub.com/'

def node2text(node):
    if node.name == None:
        if '您目前所在的地区' in node:
            return ''
        else:
            string = node
            string = re.sub('\&quot;', "\"", string)
            string = re.sub('\&amp;', "&", string)
            string = re.sub('\&ldquo;', "\"", string)
            string = re.sub('\&rdquo;', "\"", string)
            string = demoji.replace(string)
            return string
    elif node.name == 'br':
        return '\n\n'
    elif node.name in ['img', 'a']:
        return '\n'
    elif node.name == 'video':
        return '\n[video]' + node['src'] + '[/video]\n'
    else:
        if node.name in ['b', 'strong']:
            start = '[b]'
            end = '[/b]'
        elif node.name == 'u':
            start = '[u]'
            end = '[/u]'
        elif node.name in ['i', 'em']:
            start = '[i]'
            end = '[/i]'
        elif node.name == 'li':
            start = '[*]'
            end = '\n'
        elif node.name in ['ul',]:
            start = '\n'
            end = ''
        elif node.name in ['h1', 'h2', 'h3', 'h4']:
            start = '\n[center][u][b]'
            end = '[/center][/u][/b]\n'
        elif node.name == 'p':
            start = '\n'
            end = ''
        else:
            start = ''
            end = ''
        string = start
        for child in node.children:
            string += node2text(child)
        return string + end

def html2bb(data):
    soup = BeautifulSoup(data, 'lxml')
    string = node2text(soup)
    string = re.sub('  +', " ", string)
    string = re.sub('\n +', "\n", string)
    string = re.sub('\n\n\n+', '\n\n', string)
    return string

class PicHost:
    def __init__(self, conf, logger):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers = HEADERS
        self.session.headers.update({'Referer': PTER_DOMAIN})
        cookies = dict([field.split('=', 1) for field in conf.pic_cookies.split('; ')])
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)
        self.authkey, self.userlink = self._get_authkey()
        self.imgs = self._get_imgs()

    def _get_authkey(self):
        res = self.session.get('https://s3.pterclub.com', allow_redirects=False)
        res_soup = BeautifulSoup(res.text, 'lxml')
        userlink =  res_soup.select('#top-bar-user a')[0]['href']
        authkey =  res_soup.select('#top-bar-user a')[-1]['href'].split('=')[1]
        return authkey, userlink
    
    def _get_imgs(self):
        self.logger.info('正在获取猫站图床已有图片信息...')
        page = 1
        cont = True
        imgs = {}
        page_url = self.userlink + '/?list=images&sort=title_asc&page=1'
        while(cont):
            self.logger.info('第' + str(page) + '页...')
            res = self.session.get(page_url, allow_redirects=False)
            res_soup = BeautifulSoup(res.text, 'lxml')
            images =  res_soup.select('.list-item-image img')
            for image in images:
                name = image['alt']
                url = re.sub(r'\.md\.jpg$', '.jpg', image['src'])
                imgs[name] = url
            no_next_page = res_soup.select('.pagination-next.pagination-disabled')
            if no_next_page:
                cont = False
            else:
                next_page = res_soup.select('.pagination-next a')
                if not next_page:
                    cont = False
                else:
                    page_url = next_page[0]['href']
                    page += 1
                    time.sleep(3)
        self.logger.info('完成猫站图床已有图片信息获取')
        return imgs
    
    def upload(self, link):
        name = re.findall('\w+\.jpg$', link)[-1]
        if name in self.imgs.keys():
            return self.imgs[name]
        else:
            timestamp = int(datetime.datetime.now().timestamp()*1000)
            data = {'source':link, 'type': 'url', 'action':'upload', 'timestamp':str(timestamp), 'auth_token': self.authkey, 'nsfw':'0'}
            res = self.session.post('https://s3.pterclub.com/json', data=data).json()
            self.imgs[name] = res['image']['image']['url']
            return self.imgs[name]

class GoGApi:
    def __init__(self, logger, conf, picHost, entry):
        self.logger = logger
        self.conf = conf
        self.picHost = picHost
        self.entry = entry

        self.session = requests.Session()
        self.session.headers = HEADERS
        if self.conf.proxies:
            self.session.proxies ={'http': self.conf.proxies, 'https': self.conf.proxies}

        self.game = entry.game
        self.store_url = 'https://www.gog.com/game/' + self.game
        self.store_en_url = 'https://www.gog.com/en/game/' + self.game
        self.gog_games_url = 'https://gog-games.com/game/' + self.game

        self.id = ''
        #self.api_en_url = ''
        self.api_zh_url = ''

        self.info = {}
        self.info['torrent_title'] = self.game
        self.info['scene'] = 'no'
        self.info['verified'] = 'yes'
        self.info['release_type'] = {}
        self.info['release_type']['main'] = '1' # Game
        self.info['release_format'] = {}
        self.info['release_format']['main'] = '5' # DRM Free
        self.info['release_format']['goodies'] = '7' # Other
        self.info['release_title'] = {}
        title1 = re.sub('\.exe$', '', self.entry.exe_file) + '-GOG'
        version_to_end = re.search(r'(\d+\.)+\d+.*', title1)
        if version_to_end:
            self.info['release_title']['main'] = 'v' + version_to_end[0].replace('_', ' ')
        else:
            self.info['release_title']['main'] = re.search(r'(\d{5}|\().*', title1)[0].replace('_', ' ')
        self.info['release_title']['goodies'] = 'Goodies-GOG'
        self.info['torrent_desc'] = {}
        self.info['torrent_desc']['goodies'] = ''
        if entry.goodies:
            self.info['torrent_desc']['goodies'] += ', '.join(entry.goodies) + ' from GOG'
            self.info['release_type']['goodies'] = GOODIES_TYPE[entry.goodies[0]]


    # 加载cookie到session，越过18岁提醒
    def _install_cookies(self):
        cookies = {'gog_wantsmaturecontent':'18'}
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)

    def get_info(self):
        self.logger.info('获取游戏信息...')
        self._install_cookies()
        self.session.headers.update({'Referer': 'https://www.gog.com/'})
        # 从英文商店页面获取英文名、游戏id
        try:
            res = self.session.get(self.store_en_url, timeout=60, allow_redirects=False)
            if res.status_code == 302:
                raise ValueError
        except:
            self.logger.error('自动获取商店信息失败，请手动输入输入商店页面url（https://www.gog.com/en/game/*）')
            self.game = utils.true_input('只需输入*代表的部分：')
            self.store_url = 'https://www.gog.com/game/' +  self.game
            self.store_en_url = 'https://www.gog.com/en/game/' + self.game
            self.gog_games_url = 'https://gog-games.com/game/' + self.game
            try:
                res = self.session.get(self.store_en_url, timeout=60, allow_redirects=False)
                if res.status_code == 302:
                    raise ValueError
            except:
                self.entry.status = 'ignored'
                self.entry.info = self.entry.transfer_path + '无法获取到商店信息，忽略'
                self.logger.error(self.entry.info)
                self.entry.ignore()
                return False
        res_soup = BeautifulSoup(res.text, 'lxml')
        for div in res_soup.body.select('div'):
            if div.has_attr('card-product'):
                self.id = div['card-product']
                break
        self.info['name'] = res_soup.select('h1')[0].get_text().replace('\u2122', '')
        #self.api_en_url = 'https://api.gog.com/v2/games/' + self.id + '?locale=en-US'
        self.api_zh_url = 'https://api.gog.com/v2/games/' + self.id + '?locale=zh-Hans'

        time.sleep(0.5)
        # 从中文api接口获取各项信息
        self.session.headers['Referer'] = self.store_url
        try:
            res = self.session.get(self.api_zh_url, timeout=60).json()
        except:
            self.status = 'ignored'
            self.entry.info = self.entry.transfer_path + '无法获取到API信息，忽略'
            self.logger.error(self.entry.info)
            self.entry.ignore()
            return False
        self.info['chinese_name'] = res['_embedded']['product']['title'].replace('\u2122', '')
        if self.conf.use_pic_host:
            self.info['cover'] = self.picHost.upload(res['_links']['boxArtImage']['href'])
        else:
            self.info['cover'] = res['_links']['boxArtImage']['href']
        self.info['platform'] = []
        self.info['min_req'] = {}
        self.info['rcmd_req'] = {}
        for plat in res['_embedded']['supportedOperatingSystems']:
            self.info['platform'].append(PLATFORM_NAME[plat['operatingSystem']['name']])
            if plat['operatingSystem']['name'] == 'windows':
                target_req = None
                for requirment in plat['systemRequirements']:
                    if requirment['type'] == 'minimum':
                        target_req = self.info['min_req']
                    elif requirment['type'] == 'recommended':
                        target_req = self.info['rcmd_req']
                    else:
                        continue
                    for req in requirment['requirements']:
                        if req['description']:
                            target_req[REQ_NAME[req['id']]] = req['description']
        self.info['screenshot'] = []
        for screenshot in res['_embedded']['screenshots']:
            link_without_formatter = screenshot['_links']['self']['href']
            formatters = screenshot['_links']['self']['formatters']
            for frmt in formatters:
                if 'product_' in frmt:
                    formatter = frmt
            if not formatter:
                formatter = formatters[1]
            link = link_without_formatter.replace('{formatter}', formatter)
            # 转存到猫站图床
            if self.conf.use_pic_host:
                link = self.picHost.upload(link)
            self.info['screenshot'].append(link)
        if not 'globalReleaseData' in res['_embedded']['product'].keys():
            self.info['release_date'] = res['_embedded']['product']['gogReleaseDate'].split('T')[0]
        else:
            self.info['release_date'] = res['_embedded']['product']['globalReleaseDate'].split('T')[0]
        self.info['year'] = self.info['release_date'][0:4]
        self.info['lan_text'] = []
        self.info['lan_audio'] = []
        for lan in res['_embedded']['localizations']:
            if lan['_embedded']['localizationScope']['type'] == 'text':
                self.info['lan_text'].append(lan['_embedded']['language']['code'])
            elif lan['_embedded']['localizationScope']['type'] == 'audio':
                self.info['lan_audio'].append(lan['_embedded']['language']['code'])
        self.info['torrent_desc']['main'] = '字幕语言：' + '，'.join([LAN_NAME[code] for code in self.info['lan_text']]) +'\n'
        self.info['torrent_desc']['main'] += '配音语言：' + '，'.join([LAN_NAME[code] for code in self.info['lan_audio']]) +'\n'
        self.info['genres'] = []
        for tag in res['_embedded']['tags']:
            self.info['genres'].append(tag['name'])
        self.info['property'] = []
        for prop in res['_embedded']['properties']:
            self.info['property'].append(prop['name'])
        self.info['feature'] = []
        for feature in res['_embedded']['features']:
            self.info['feature'].append(feature['name'])
        # 生成游戏描述
        self.info['description'] = html2bb(res['overview'])
        if 'featuresDescription' in res.keys():
            self.info['description'] += '\n\n[b]游戏亮点[/b]\n\n[*]' + res['featuresDescription'].replace('\n', '\n[*]')

        self.info['desc'] = f"\n[center][img]{self.info['cover']}[/img][/center]"
        self.info['desc'] += f"[center][b][u]关于游戏[/u][/b][/center]\n"
        self.info['desc'] += f"[b]发行日期[/b]：{self.info['release_date']}\n\n"
        self.info['desc'] += f"[b]相关链接[/b]：{self.store_url}\n\n"
        self.info['desc'] += f"[b]游戏标签[/b]：{'，'.join(self.info['genres'])}\n\n"
        self.info['desc'] += f"[b]游戏属性[/b]：{'，'.join(self.info['property'])}\n\n"
        self.info['desc'] += f"[b]游戏特性[/b]：{'，'.join(self.info['feature'])}\n\n"
        self.info['desc'] += f"[center][b][u]配置要求[/u][/b][/center]\n"
        self.info['desc'] += f"[b]最低配置[/b]\n\n"
        for req_key in self.info['min_req'].keys():
            self.info['desc'] += f"[*][b]{req_key}：[/b]{self.info['min_req'][req_key]}\n"
        self.info['desc'] += f"\n\n[b]推荐配置[/b]\n\n"
        for req_key in self.info['rcmd_req'].keys():
            self.info['desc'] += f"[*][b]{req_key}：[/b]{self.info['rcmd_req'][req_key]}\n"
        self.info['desc'] += '\n\n' + self.info['description'] + '\n'
        self.info['desc'] += '[center]'
        for screen in self.info['screenshot']:
            self.info['desc'] += '[img]{}[/img]\n'.format(screen)
        self.info['desc'] += '[/center]'
        self.entry.game_info = self.info
        self.logger.info('从商店获取游戏信息成功')
        self.logger.debug(self.info)
        return True

class PTerApi:
    def __init__(self, logger, conf, entry):
        self.logger = logger
        self.conf = conf
        self.entry = entry

        self.session = requests.Session()
        self.session.headers = HEADERS
        if self.conf.proxies:
            self.session.proxies ={'http': self.conf.proxies, 'https': self.conf.proxies}

        self.platform = 'Windows' if 'Windows' in entry.game_info['platform'] else entry.game_info['platform'][0]
        self.gid = None
        self.uplver = conf.anonymous

        self.torrent_ids = []
        self.error_info = ''

    # 加载cookie到session
    def _install_cookies(self):
        self.session.headers.update({'Referer': PTER_DOMAIN})
        if self.conf.pter_cookies:
            cookies = dict([field.split('=', 1) for field in self.conf.pter_cookies.split('; ')])
            self.session.cookies = requests.utils.cookiejar_from_dict(cookies)
        else:
            return None

    def _find_game(self):
        print('将要上传的种子是：{}'.format(self.entry.game_info['release_title']))
        print('对应的游戏是：{}'.format(self.entry.game_info['name']))
        # 搜索游戏
        url = PTER_DOMAIN + 'searchgameinfo.php?name=' + self.entry.game_info['name']
        res = self.session.get(url)
        res_soup = BeautifulSoup(res.text, 'lxml')
        game_list = res_soup.select('a[title="点击发布这游戏设备的种子"]')
        platform_list = res_soup.select('img[src^="/pic/category/chd/scenetorrents/"]')
        if not game_list:
            return None
        game_dict = {}
        num = 1
        # 获取游戏列表
        for game, platform in zip(game_list[::2], platform_list):
            gid = re.search(r'detailsgameinfo.php\?id=(\d+)', game['href']).group(1)
            game_dict[str(num)] = '{}: {} GID:{}'.format(platform['title'], game.text, gid)
            num += 1
        # 选择上传的目标游戏
        print('我们在猫站找到以下游戏，请选择要上传的游戏分组的编号(并非gid)，如果没有请输入0：')
        for num, game in game_dict.items():
            print('{}.{}'.format(num, game))
        gid = (utils.true_input('编号： '))
        if gid == '0':
            return None
        self.logger.debug('选择的游戏是：' + game_dict[gid])
        gid = re.search(r'GID:(.+)', game_dict[gid]).group(1)
        self.gid = gid
        return gid

    # 上传游戏
    def _upload_game(self):
        url = PTER_DOMAIN + 'takeuploadgameinfo.php'
        data = {'uplver': self.uplver, 'detailsgameinfoid': '0', 'name': self.entry.game_info['name'], 'color': '0', 'font': '0',
                'size': '0', 'descr': self.entry.game_info['desc'], 'console': PLATFORM_DICT[self.platform],
                'year': self.entry.game_info['year'],
                'has_allowed_offer': '0',
                'small_descr': self.entry.game_info['chinese_name']}
        cont = utils.check_yes('确认要添加游戏' + self.entry.game_info['name'] + '？[Y]/N:', True)
        if cont:
            game_url = self.session.post(url, data=data).url
            gid = re.search(r'detailsgameinfo.php\?id=(\d+)', game_url).group(1)
            self.gid = gid
            self.logger.info('上传游戏的GID是：' + self.gid)
            return True
        else:
            return False

    # 上传游戏
    def _upload_torrent(self):
        url = PTER_DOMAIN + 'takeuploadgame.php'
        region = ''
        # 游戏主体 或 Goodies
        for t_type in self.entry.torrent.keys():
            # 文件名和文件指针
            file = ("file", (os.path.basename(self.entry.torrent[t_type]), open(self.entry.torrent[t_type], 'rb'), 'application/x-bittorrent')),
            # 各类种子信息和标签
            data = {'uplver': self.uplver, 'categories': self.entry.game_info['release_type'][t_type],
                    'format': self.entry.game_info['release_format'][t_type],
                    'has_allowed_offer': '0', 'gid': self.gid,
                    'descr': self.entry.game_info['torrent_desc'][t_type]}
            if t_type != 'goodies':
                region = utils.true_input('请选择种子地区（直接输入数字即可）：\n1.大陆\n2.香港\n3.台湾\n4.英美\n5.韩国\n6.日本\n7.印度\n8.其它\n')
            # 各类标签
            if self.entry.game_info['scene'] == 'yes':
                data['sce'] = self.entry.game_info['scene']
            if self.entry.game_info['verified'] == 'yes':
                data['vs'] = self.entry.game_info['verified']
            #if '视觉小说' in self.entry.game_info['genres']:
            #    data['gg'] = 'yes'
            if 'cn' in self.entry.game_info['lan_text']:
                data['zhongzi'] = 'yes'
            if 'cn' in self.entry.game_info['lan_audio']:
                data['guoyu'] = 'yes'
            # 地区，影响游戏的标签
            data['team'] = region
            # 种子标签
            user_title = input('智能检测到的游戏种子标题为{}，若有错误，请输入正确的标题，没有请直接回车：'.format(self.entry.game_info['release_title'][t_type]))
            user_title = self.entry.game_info['release_title'][t_type] if user_title == '' else user_title
            data['name'] = user_title
            self.logger.debug(data)
            # 上传
            self.logger.info('正在上传... ...')
            res = self.session.post(url, data=data, files=file)
            status = re.findall('\w+=\d+', res.url)
            if (not status) or status[1] != 'uploaded=1':
                res.encoding = 'utf-8'
                error_soup = BeautifulSoup(res.text, 'lxml')
                e_info = error_soup.select_one('h2+table td.text')
                if e_info:
                    e_info = e_info.text
                else:
                    e_info = error_soup.find('h1').find_next()
                self.error_info = '上传失败：{}'.format(e_info)
                return False
            else:
                self.torrent_ids.append(status[0].split('=')[1])

    def worker(self):
        self._install_cookies()
        print('正在搜索猫站游戏列表...')
        self._find_game()
        # 未找到游戏或用户选择无对应游戏的情况下，上传游戏
        if self.gid is None:
            self.logger.info('未找到相关游戏，正在上传游戏资料...')
            if self._upload_game() is False:
                self.entry.status = 'ignored'
                self.entry.info = '游戏放弃上传或上传失败：' + self.entry.game_info['name']
                self.logger.error(self.entry.info)
                self.entry.ignore()
                return False
        print('正在上传种子...')
        if self._upload_torrent() is False:
            self.entry.status = 'ignored'
            self.entry.info = '游戏 ' + self.entry.game_info['name'] +'上传失败：' + self.error_info
            self.logger.error(self.entry.info)
            self.entry.ignore()
            return False
        else:
            self.entry.info = '已上传'
            self.entry.status = 'uploaded'
            if self.conf.seed:
                for torrent_id in self.torrent_ids:
                    download_url = PTER_DOMAIN + 'download.php?id=' + torrent_id
                    torrent = self.session.get(download_url)
                    if self.conf.client_type == 'tr':
                        tr = transmission_rpc.Client(host=self.conf.client_ip, port=self.conf.client_port, username=self.conf.client_username, password=self.conf.client_password)
                        tr.add_torrent(torrent.content, download_dir=os.path.join(self.conf.save_path, self.entry.renamed_path), paused=True)
                    elif self.conf.client_type == 'qb':
                        qb = qbittorrentapi.Client(host=self.conf.client_ip, port=self.conf.client_port, username=self.conf.client_username, password=self.conf.client_password)
                        qb.torrents_add(torrent_files=torrent.content, save_path=os.path.join(self.conf.save_path, self.entry.renamed_path), is_paused=True)
            self.entry.complete()
            self.logger.info(self.entry.info)
            return True
