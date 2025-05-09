import configparser
import os
import re
import time
from typing import Dict, List, Pattern, Tuple
import yaml

class RegexMatcher:
    def __init__(self, yaml_file: str):
        self.patterns: Dict[str, Pattern] = {}
        self.load_patterns(yaml_file)

    def load_patterns(self, yaml_file: str) -> None:
        """从YAML文件加载正则表达式并预编译"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for group in data.get('rules', []):
            if 'group' in group:
                tmp = self.patterns.setdefault(group["group"],{})
            if 'rule' in group:
                for rule in group['rule']:
                    pattern = re.compile(rule['f_regex'])
                    tmp[rule['name']] = pattern

    def find_matches(self, content: str) -> Dict[str, List[Tuple[str, str]]]:
        """在内容中查找所有匹配项，并记录每个匹配项对应的正则名"""
        results = {}

        for name, pattern in self.patterns["FindLink"].items():
            # start_time = time.time()
            matches = pattern.findall(content)
            # end_time = time.time()
            # print(name,end_time - start_time)
            for match in matches:
                # 如果匹配结果是元组列表，获取第一个元素
                match_str = match if isinstance(match, str) else match[0]
                results.setdefault(match_str,set()).add(name)

        # print(results)
        # 第二轮排除
        for match_str in list(results.keys()):
            for exclude_name, exclude_pattern in self.patterns["excludeLink"].items():
                if exclude_pattern.match(match_str):
                    del results[match_str]
                    # print(f"Excluded by {exclude_name}: {match_str}")
                    break

        return results

def loadParamData(config_path="paramdict.yml",ParamSwitch=False):
    if os.path.exists(config_path) and ParamSwitch:
        with open(config_path, "r", encoding="utf-8") as f:
            param_data = yaml.safe_load(f)
    else:
        param_data = None
    return param_data

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
        'Proxies': 'http://127.0.0.1:9091',
        '# fuzz参数字典开关': None,
        'ParamSwitch': True,
        '# 扫描范围,*匹配所有': None,
        'SubDomain':'*.cgbchina.com.cn'
    }
    config['REGEX'] = {
        '# 移除URL上下文': None,
        'RemoveUrlContext': '(https?://[^/]+)/[^/]+(/.*)'
    }
    config['EXTRACTOR']={
        '# 排除大文件后缀': None,
        'A':'.css,.png,.jpg,.ico,.jepg,.exe,.zip,.dmg,.pdf'
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)

# 创建匹配器实例
matcher = RegexMatcher('rules.yml')
config = initialize_config()
param_data = loadParamData(ParamSwitch=config.getboolean('CRAWLER','ParamSwitch'))



# 爬虫爬取深度
crawler_MaxDepth = config['CRAWLER']['MaxDepth']
crawler_MaxRetries = config['CRAWLER']['MaxRetries']
crawler_SubDomain = config['CRAWLER']['SubDomain']
crawler_Proxies = {"http://": config['CRAWLER']['Proxies'],"https://": config['CRAWLER']['Proxies']}


