import os
import re
import utils

class GameHashTable():
    def __init__(self, logger):
        self.logger = logger

        self.src_dir = 'gog-games'
        self.src = os.path.join(self.src_dir, 'gog_collection.sfv')
        self.version = ''
        self.htable = {}
        self.ntable = {}
        self._get_repo()
        self._gen_hash_table()

    # pull git repo
    def _get_repo(self):
        pass
        #if not os.path.exists(self.src_dir):
        #    self.logger.info('-------- Cloning gog game repo ------------')
        #    os.system('git clone https://github.com/GOG-Games-com/GOG.com-Game-Collection-Verification')
        #    self.logger.info('----------------- Done --------------------')
        #else:
        #    self.logger.info('-------- Updating gog game repo ------------')
        #    os.system('cd ' + self.src_dir + '; git fetch; git merge origin/main')
        #    self.logger.info('----------------- Done --------------------')

    # create hash-game table from sfv file
    def _gen_hash_table(self):
        with open(self.src) as f:
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
                            filename = game_filename[1]
                            self.htable[crc] = game
                            self.ntable[filename] = game
                        else:
                            print('Failed to parse line:' + line)
        self.version = os.popen('cd ' + self.src_dir + '; git rev-parse HEAD').read()

    def update(self):
        self._get_repo()
        cur_version = os.popen('cd ' + self.src_dir + '; git rev-parse HEAD').read()
        if cur_version != self.version:
            self._gen_hash_table()

    def search(self, crc):
        crc = crc.lower()
        if crc in self.htable.keys():
            return self.htable[crc]
        else:
            return ''

    def guess(self, game):
        print(game)
        for k in self.ntable.keys():
            if game in k:
                print('猜测到可能的游戏名为：', self.ntable[k])
                right = utils.check_yes('是否正确[Y/[N]：')
                if right:
                    return self.ntable[k]
        return ''