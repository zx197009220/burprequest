import configparser
import os


def initialize_config(config_path="config.ini"):
    """初始化配置文件，若不存在则创建默认配置"""
    if not os.path.exists(config_path):
    # if True:
        create_default_config(config_path)
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read("config.ini", encoding='utf-8')
    return config

def create_default_config(config_path):

    config = configparser.RawConfigParser(allow_no_value=True)
    """生成默认配置模板"""
    config['CRAWLER'] = {
        '# 最大爬取深度': None,
        'MaxDepth': 5,
        '# 最大失败重试次数': None,
        'MaxRetries': 3,
        '# 代理地址': None,
        'Proxies': 'http://127.0.0.1:9091'
    }
    config['REGEX'] = {
        '# 移除URL上下文': None,
        'RemoveUrlContext': '(https?://[^/]+)/[^/]+(/.*)'
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)



config = initialize_config()




# 爬虫爬取深度
crawler_MaxDepth = config['CRAWLER']['MaxDepth']
crawler_MaxRetries = config['CRAWLER']['MaxRetries']
crawler_Proxies = {"http://": config['CRAWLER']['Proxies'],"https://": config['CRAWLER']['Proxies']}
regex_RemoveUrlContext = config['REGEX']['RemoveUrlContext']

