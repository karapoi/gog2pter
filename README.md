# gog2pter快捷转种工具![python](https://img.shields.io/badge/python-3.7-blue)![time](https://img.shields.io/github/last-commit/karapoi/gog2pter)<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)<!-- ALL-CONTRIBUTORS-BADGE:END -->

# 重要提示 Important Note
```diff
- 请勿以任何方式在此求邀（包括但不限于issue、discussion、PR）

- Plese don't ask for any invite here, this is not your place!
```

## 简介

该脚本能够在检测gog games下载的文件后自动获取相关信息并制作种子，同时自动将种子上传至PTerClub

---
## 工具特点
* 自动分析指定目录下的游戏文件，分析获取游戏名
* 自动制种，方便配合BT客户端实现自动做种
* 自动从gog商店获取游戏信息
* 自动新建PTer游戏条目
* 自动上传游戏种子
* 支持 `游戏本体` `Goodies`分别自动制种

## 依赖环境 

###  python模式

* Python 3
* Git
* Mac, Linux, Windows

## 安装指南

### Python 模式

#### 1.克隆我的仓库
由于项目依赖于GOG-Games-com/GOG.com-Game-Collection-Verification，请添加--recursive选项
~~~~shell
git clone --recursive https://github.com/karapoi/gog2pter.git
~~~~
#### 2.安装相关依赖
~~~~shell
pip install -r requirements.txt
~~~~
如果你无法安装的话可能是你的用户权限不够，尝试使用`sudo`安装；对于某些同时装有`python2` 与 `python3` 的用户，可能需要指明`pip`的版本，如 `pip3`
~~~~shell
sudo -H pip install -r requirements.txt
~~~~
#### 3.运行使用
##### 3.1 gog2pter
~~~~shell
mkdir config
python main.py
~~~~
另外可以使用以下命令来查看可以的命令选项和说明：
~~~~shell
python main.py --help
~~~~
##### 3.2 find games
发现可能尚未发布的游戏，注意最好发布前再手动搜索确认一次~
需要完成gog2pter的配置后才能使用。
~~~~shell
python find_games.py
~~~~
## 使用指南

### 1.填写配置信息
第一次运行时，程序会让你填写一些配置信息，按照实际情况填写即可：
* 猫站`cookies`
* 猫站`passkey`
* 匿名选项
* 数据目录（即自动检测的目录）
* 是否启用上传目录（强烈建议同硬链接模式一同启用）
* 是否启用硬链接模式（强烈建议启用）
* 种子目录（种子的保存目录）

### 2 填写cookies
第一次运行程序时，程序会让你输入猫站的cookies，按照提示输入即可：
![cookies.png](https://img.pterclub.com/images/2021/03/15/2021-03-15-223914.png)
cookies在登录猫站的情况下，按F12打开调试窗口，在控制台中输入document.cookie即可获得，注意不包括前后的引号。
也可按照常见问题所述方法获取。

### 3.等待程序运行

### 4.选择游戏信息
如果程序认为将要上传的种子的游戏信息可能已经存在于猫站，会返回一个列表让你选择游戏信息，如果不存在相关游戏的话，系统会自动上传到猫站。
```shell
我们在猫站找到以下游戏，请选择要上传的游戏分组（输入编号(并非gid)即可，如果没有请输入0）：
1.Windows: Cooking Simulator GID:3409
编号： <输入编号>
```

### 5.输入种子额外信息
由于无法从gog获取游戏地区的相关信息，需要用户手动输入：
![moreinfo.png](https://img.pterclub.com/images/2021/03/15/2021-03-15-224809.png)

### 6.审查种子标题
脚本会自动检测主安装文件（即文件夹下符合set_*.exe命名的名字最短的文件）的名字并生成符合猫站规则的标题，但是仍然需要用户进行检查。如果有错误请输入正确的标题，无误则直接回车。

### 7.上传Goodies
脚本会自动检测目录下的zip或rar文件，并将其视作Goodies单独建立文件夹，单独制种，单独上传，其标题也需要用户进行检查。如果有错误请输入正确的标题，无误则直接回车。

### 8.上传完成

## 常见问题
* Q. cookies 是个什么东西呀?怎么获取呀？
* A. cookie 是来存储你登陆信息的一串字符，下面我以firefox为例演示一下怎么获取。
* * 按下F12进入开发者工具，并切换至`NETWORK/网络`栏目：
* * ![Network.png](https://img.pterclub.com/images/2021/03/22/10ac0ff23048ed11c.png)
* * 单击你左上角的用户名，载入你的用户界面
* * 找到`NEWWORK/网络`栏目里加载出来的user.php之类文件，并单击它：
* * ![user.php.png](https://img.pterclub.com/images/2021/03/23/2.png)
* * 找到`request header/请求头` 中cookie项目中的字段并复制下来：
* * ![cookies.png](https://img.pterclub.com/images/2021/03/22/3abed1483ad76c9a6.png)

-->

## 贡献者 ✨

脚本编写过程中大量参考了[ggn2pter](https://github.com/inerfire/ggn2pter)，同时，部分内容参考了[happyfunc](https://github.com/inerfire/happyfunc)在此对原作者提出感谢。

感谢以下诸位的共同协作:

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/karapoi"><img src="https://avatars.githubusercontent.com/u/9048968?v=4?s=100" width="100px;" alt=""/><br /><sub><b>karapoi</b></sub></a><br /><a href="https://github.com/karapoi/gog2pter/commits?author=karapoi" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
