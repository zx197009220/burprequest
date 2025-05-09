import re
from urllib.parse import urlparse, urljoin
import os
from config import matcher,param_data,crawler_SubDomain
from log import setup_logger

loggerLink = setup_logger('matchlinks', 'matchlinks.log',add_console_handler=False)
loggerExcluelink = setup_logger('excludeLink', 'excludelinks.log',add_console_handler=False)
# 正则表达式匹配<a>标签的href属性
newline_pattern = re.compile(r'\n')
# 正则表达式匹配<a>标签的src属性
src_pattern = re.compile(r'src\s*=\s*["\'](.*?)["\']', re.IGNORECASE)

# 正则表达式匹配<link>标签的href属性
href_pattern = re.compile(r'href\s*=\s*["\'](.*?)["\']', re.IGNORECASE)

# 正则表达式匹配http开头
http_pattern = re.compile(r'(http[s]?://[\w/\?=#;,\.\-_:&;]+)')

# 正则表达式匹配引号内的接口
api_pattern = re.compile(r'["\'](\.{0,2}/[\w/\?=#;,\.\-_:&;]+)["\']')

#正则匹配引号内非/开头的接口，需排除Content-Type
api1_pattern = re.compile(r'["\']([a-zA-Z0-9\-_]{1,50}/[a-zA-Z0-9\-_]{1,50}/[\w/\?=#;,\.\-_:&;]+)["\']')

#正则排除Content-Type
content_type_pattern = re.compile(r'\b(text|application|multipart)\/(css|plain|javascript|x-www-form-urlencoded|octet-stream|json|html|form-data)\b')

#匹配=号参数，或者/:item类型参数
param_regex = re.compile(r'(\w+)=([\w]*)|/:(\w+)')
# 输入参数yd03
# param_data = {"redirectUri":"http://www.baidu.com","webViewUrl":"http://www.baidu.com","itemId": "119100100777004", "userId": "166053", "shopId": "2100191001", "orderId": "40538079003","reverseOrderId":"10535793001","urgeId": "1349044","id":"11","asid":"11","skuOrderId":"1111","code":"11","activityId":"111"}
param_dict = {}




async def parse_links(html_content,source_url,depth_Parent=0):
# def parse_links(html_content,source_url,depth_Parent=0):


    html_content = newline_pattern.sub('', html_content)




    # 查找匹配项
    matches = matcher.find_matches(html_content)


    urls = {}

    depth_Child = 0
    loggerLink.info(f"【send request】【{depth_Parent}】{source_url}")
    loggerExcluelink.info(f"【send request】【{depth_Parent}】{source_url}")
    for link, regex_names in matches.items():
        # print(link, regex_names)
        res = normalize_link(link,source_url)
        if res:
            urlFuzz, url = res
            depth_Child += 1
            depth = f"{depth_Parent}.{depth_Child}"
            loggerLink.info(f"【{urlFuzz}】【{depth}】{regex_names}{url}")
            urlProperty = (urlFuzz,depth)
            urls.setdefault(url,urlProperty)
        else:
            continue
    return urls


def get_extension(path):
    """从文件路径中提取扩展名"""
    _, ext = os.path.splitext(path)
    return ext

def is_subdomain(domain,subdomain="*.cgbchina.com.cn"):

    pattern = subdomain.replace(".","\.").replace("*",".*")
    return re.match(pattern, domain) is not None

def baseurl(source_url):

    url_parse = urlparse(source_url)
    return url_parse.scheme+"://"+url_parse.netloc

def add_context(link,source_url):

    url = urlparse(source_url)
    context = url.path.split("/")[1] if url.path != "" else ""

    link = link if link.startswith("/") else "/"+link
    path = re.sub(r'\./|\.\./', '', link)

    if context in path:
        # return context+link if link.startswith(("/herd","/design","/scripts")) else link
        return url.scheme+"://"+url.netloc+path
    else:
        return url.scheme+"://"+url.netloc+"/"+context+path

def is_exclusion_rules(link,url,url_status,source_url):
    # 解析链接
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # 是否是目标域名
    if not is_subdomain(domain,crawler_SubDomain):
        loggerExcluelink.info(f"【{url_status}】{url}")
        return True
    # 去除文本类型
    if content_type_pattern.match(link):
        return True

    # 获取链接的扩展名
    extension = get_extension(parsed_url.path)
    if extension.lower() in [".css",".png",".jpg",".ico",".jepg",".exe",".zip",".dmg",".pdf"]:
        loggerExcluelink.info(f"【{url_status}】{url}")
        return True

    return False

def normalize_link(link,source_url):

    if link.startswith("http"):
        url_status = "source"
        url = link
    elif link.startswith("//") and is_subdomain(link):
        url_status = "source"
        url = urlparse(source_url).scheme+":"+link
    else:
        url_status = "fuzz"
        url = add_context(link,source_url)


    if is_exclusion_rules(link,url,url_status,source_url):
        return
    else:
        url = fuzz(url,param_data)
        return url_status, url


def param_count(param):
    param_dict.setdefault(param, 0)
    param_dict[param] += 1

def fuzz(url, data):
    # 合并后的正则表达式，匹配查询参数和路径参数
    # 匹配形式如 ?param1=value1&param2=value2 或 /:param1/value1/:param2/value2
    # 替换函数
    if data is None:
        return url
    def replacer(match):

        if match.group(2)=="":
            param_count(match.group(1))
        # 如果是查询参数或路径参数的键值对形式，如 ?param=value 或 /:param/value
        if match.group(1):  # 如 ?param=value
            return f"{match.group(1)}={data.get(match.group(1),match.group(2))}"
        # 如果是路径参数的形式，
        elif match.group(3):  # 如 /:param
            param_count(match.group(3))
            return f"/{data.get(match.group(3), ':' + match.group(3))}"
    return param_regex.sub(replacer, url)

if __name__ == '__main__':
    with open("20250508.js","r",encoding="utf-8")as f:
        content = f.read()

    parse_links(content,"https://necp-yd03.test.cgbchina.com.cn/assets/js/app-f075b844-835d2378794369d5f62d.js")
    exit()
