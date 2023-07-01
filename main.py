import configparser
import argparse
import os
import json
import site_api
import time
import pickle
import atexit
import utils
from Configuration import Configuration
from Entry import Entry
from GameHashTable import GameHashTable

parser = argparse.ArgumentParser(description='gog2pter是协助将gog下载的文件发布到猫站的工具。')
parser.add_argument('--reinit', action='store_true', help='重新设置配置参数')
parser.add_argument('--cookies', action='store_true', help='重新设置cookies')
parser.add_argument('--reconfig', action='store_true', help='从配置文件和cookies.json中重新加载配置')
parser.add_argument('-i', '--ignored', action='store_true', help='打印忽略条目列表')
parser.add_argument('-c', '--completed', action='store_true', help='打印完成条目列表')
parser.add_argument('-r', '--remove', type=str, help='从完成和忽略条目列表中移除该条目')
parser.add_argument('-a', '--add', type=str, help='添加条目到忽略条目列表')
args = parser.parse_args()

conf = None
gtable = None

def initial(logger):

    global conf
    global gtable

    utils.check_dir('config')

    if 'cookies.json' not in os.listdir('config'):
        logger.warning('cookies文件不存在')
    elif args.cookies:
        logger.info('重新生成cookies文件')
    if 'cookies.json' not in os.listdir('config') or args.cookies:
        cookie = utils.true_input('请输入PTer的cookies：')
        cookies = {"pter": cookie}
        cookie = utils.true_input('请输入猫站图床的cookies(如不需要使用请留空)：')
        cookies['pic'] = cookie
        print(cookies)
        with open('config/cookies.json', 'w') as coo:
            json.dump(cookies, coo)

    if 'config.ini' not in os.listdir('config'):
        logger.warning('检测到config文件不存在，接下来将引导生成配置文件')
    elif args.reinit:
        logger.info('重新生成配置文件')
    if 'config.ini' not in os.listdir('config') or args.reinit:
        config = configparser.ConfigParser()

        upload_dir_on = utils.check_yes('转移数据到上传目录([Y]/N)：', True)
        if upload_dir_on:
            hlink_on = utils.check_yes('启用硬链接功能，如启用则复制文件到上传目录([Y]/N)：', True)
        else:
            hlink_on = False

        proxies = input('请输入代理地址（如socks5://192.168.1.5:7890, socks5h://192.168.1.5:7890）不使用代理请留空：')
        passkey = input('请输入猫站passkey：')
        if not passkey:
            logger.critical('passkey无效，程序中止...')
            exit()
        use_pic_host = False
        if cookies['pic']:
            use_pic_host = utils.check_yes('是否转移图片到猫站图床(Y/[N])：')
            
        check_compressed = utils.check_yes('是否检查压缩文件完整性(Y/[N])：')

        comment = input('个性种子备注(默认为空)：')

        anonymous = utils.check_yes('是否匿名发布(Y/[N])：')

        data_dir = input('请输入数据目录[./data]：') or 'data'
        utils.check_dir(data_dir)

        torrent_dir = input('请输入种子目录[./torrents]：') or 'torrents'
        utils.check_dir(torrent_dir)

        if upload_dir_on:
            upload_dir = input('请输入上传目录[./upload]：') or 'upload'
            utils.check_dir(upload_dir)
        else:
            upload_dir = ''

        seed = utils.check_yes('是否推送种子到发种客户端(Y/[N])：')

        if seed:
            client_type = input('请输入发种客户端类型([qb]/tr)：')
            if client_type != 'tr':
                client_type = 'qb'
            client_ip = input('请输入发种客户端IP[192.168.1.2]：')
            client_port = input('请输入发种客户端端口号[9091]：')
            client_username = input('请输入发种客户端用户名[admin]：')
            client_password = input('请输入发种客户端密码[adminadmin]：')
            save_path = input('请输入最终数据目录（如upload目录）在发种客户端映射的路径[/downloads]：')
        else:
            client_type = ''
            client_ip = ''
            client_port = ''
            client_username = ''
            client_password = ''
            save_path = ''
        config['MODE'] = {'proxies': proxies, 'hlink_on':hlink_on, 'upload_dir_on':upload_dir_on, 'use_pic_host':use_pic_host, 'check_compressed': check_compressed, 'comment':comment, 'seed':seed}
        config['PTER'] = {'passkey': passkey, 'anonymous': anonymous}
        config['WORKDIR'] = {'torrent_dir':torrent_dir, 'data_dir':data_dir, 'upload_dir':upload_dir}
        config['CLIENT'] = {'type':client_type, 'ip':client_ip, 'port':client_port, 'username':client_username, 'password':client_password, 'save_path':save_path}

        with open('config/config.ini', 'w') as config_f:
            config.write(config_f)

    if 'conf.pkl' not in os.listdir('config'):
        conf = Configuration()

    if 'gtable.pkl' not in os.listdir('config'):
        gtable = GameHashTable(logger)

        print('初始化完毕，请重新运行！')
        exit()


def main():
    global conf
    global gtable

    utils.check_dir('.')
    utils.check_dir('config')

    logger = utils.init_log()

    if 'config.ini' not in os.listdir('config') or 'cookies.json' not in os.listdir('config') or 'conf.pkl' not in os.listdir('config') or 'gtable.pkl' not in os.listdir('config') or args.reinit or args.cookies:
        initial(logger)
        exit()
    else:
        utils.check_file('config/conf.pkl')
        with open('config/conf.pkl', 'rb') as f:
            conf = pickle.load(f)
        utils.check_file('config/gtable.pkl')
        with open('config/gtable.pkl', 'rb') as f:
            gtable = pickle.load(f)
            gtable.update()  

    conf_exit = False
    
    if args.reconfig:
        conf.get_config()
        conf_exit = True

    if args.ignored:
        print('\n'.join(conf.ignored_entries))
        conf_exit = True
    
    if args.completed:
        print('\n'.join(conf.completed_entries))
        conf_exit = True
    
    if args.remove:
        conf.remove_ignored_entry(args.remove)
        conf.remove_completed_entry(args.remove)
        conf_exit = True

    if args.add:
        conf.add_ignored_entry(args.add)
        conf_exit = True
    
    if conf_exit:
        exit()
        
    if conf.use_pic_host:
        picHost = site_api.PicHost(conf, logger)
    else:
        picHost = None

    entry_names = os.listdir(conf.data_dir)
    for entry_name in entry_names:
        logger.info(70*'-')
        logger.info('发现待处理项：' + entry_name)
        if not (entry_name in conf.ignored_entries or entry_name in conf.completed_entries):
            time.sleep(1)
            entry = Entry(logger, conf, gtable, entry_name)
            status = entry.transfer()
            if not status:
                conf.add_record(entry)
                continue

            status = entry.preprocess()
            if not status:
                conf.add_record(entry)
                continue

            entry.make_torrent()

            gog = site_api.GoGApi(logger, conf, picHost, entry)
            status = gog.get_info()
            if not status:
                conf.add_record(entry)
                continue
            del gog
            
            pter = site_api.PTerApi(logger, conf, entry)
            try:
                status = pter.worker()
            except Exception as e:
                print('!!!错误:',e.__class__.__name__,e)
                entry.info = '上传至猫站出错'
                logger.error(entry.info)
                conf.add_record(entry)
                continue
            if not status:
                conf.add_record(entry)
                continue
            conf.add_record(entry)
            del entry
            del pter
        else:
            logger.info('忽略...')
    logger.info('列队完成，输入任意字符退出')
    input()

@atexit.register
def save_conf():
    global conf
    global gtable
    if conf != None:
        with open('config/conf.pkl', 'wb') as pf:
            pickle.dump(conf, pf)
    if gtable != None:
        with open('config/gtable.pkl', 'wb') as pf:
            pickle.dump(gtable, pf)

if __name__ == "__main__":
    try:
        main()
    finally:
        save_conf()
