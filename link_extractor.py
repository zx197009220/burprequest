import re
from urllib.parse import urlparse, urljoin
import os
from configparser import ConfigParser

# 创建ConfigParser对象
# config = ConfigParser()

# 读取配置文件
# config.read('config.ini')

# 正则表达式匹配<a>标签的href属性
newline_pattern = re.compile(r'\n')
# 正则表达式匹配<a>标签的href属性
src_pattern = re.compile(r'src\s*=\s*["\'](.*?)["\']', re.IGNORECASE)

# 正则表达式匹配<link>标签的href属性
href_pattern = re.compile(r'href\s*=\s*["\'](.*?)["\']', re.IGNORECASE)

# 正则表达式匹配http开头
http_pattern = re.compile(r'(http[s]?://[\w/\?=#;,\.\-_:&;]+)')

# 正则表达式匹配引号内的接口
api_pattern = re.compile(r'["\'](\.{0,2}/[\w/\?=#;,\.\-_:&;]+)["\']')

#正则匹配引号内非/开头的接口，需排除Content-Type
api1_pattern = re.compile(r'["\']([a-zA-Z0-9\-_]{1,50}/[\w/\?=#;,\.\-_:&;]+)["\']')

#正则排除Content-Type
content_type_pattern = re.compile(r'\b(text|application|multipart)\/(css|plain|javascript|x-www-form-urlencoded|octet-stream|json|html|form-data)\b')

#匹配=号参数，或者/:item类型参数
param_regex = re.compile(r'(\w+)=([\w]*)|/:(\w+)')
# 输入参数yd03
param_data = {"redirectUri":"http://www.baidu.com","itemId": "119100100777004", "userId": "166053", "shopId": "2100191001", "orderId": "40538079003","reverseOrderId":"10535793001","urgeId": "1349044","redirectUrl":"http://www.baidu.com"}
param_dict = {}

async def parse_links(html_content,source_url,depth_Parent=0):


    html_content = newline_pattern.sub('', html_content)



    # 查找所有匹配的链接
    src_link = src_pattern.findall(html_content)
    href_link = href_pattern.findall(html_content)
    http_link = http_pattern.findall(html_content)
    api_link = api_pattern.findall(html_content)
    api1_link = api1_pattern.findall(html_content)

    # 合并结果并去重
    links = src_link + href_link + http_link + api_link + api1_link

    urls = {}
    # 存储爬取中获得的参数出现次数
    urllog = {}

    param_dict = {}
    depth_Child = 0
    for link in links:

        res = normalize_link(link,source_url)
        if res:
            urlFuzz, url = res
            if "html%20" in url:
                print(111)
            depth_Child += 1
            depth = f"{depth_Parent}.{depth_Child}"
            urlProperty = set_urlProperty(urlFuzz,depth)
            urls.setdefault(url,urlProperty)
            urllog.setdefault(url,urlFuzz)
        else:
            continue
    writelink("urls_100.txt", urllog, source_url)
    return urls

def set_urlProperty(urlFuzz,depth):
    urlProperty= (urlFuzz,depth)
    return urlProperty

def writelink(file,data_dict,source_url):

    with open(file, 'a', encoding='utf-8') as file:
        file.write(f"\n【send request】 {source_url}\n")
        for url,value in data_dict.items():
            file.write(f"【{value}】{url}\n")
        file.write(f"\n")

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
    if not is_subdomain(domain):
        return True
    # 去除文本类型
    if content_type_pattern.match(link):
        return True
    # 去除伪协议
    if link.lower().startswith(("about:", "javascript:","tel:","data:")):
        return True
    # 获取链接的扩展名
    extension = get_extension(parsed_url.path)
    if extension.lower() in [".css",".png",".jpg",".ico",".jepg",".exe",".zip",".dmg",".pdf"]:
        writelink("errorurl.txt", {url: url_status}, source_url=source_url)
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
        return url_status, url


def param_count(param):
    param_dict.setdefault(param, 0)
    param_dict[param] += 1

def fuzz(url, data):
    # 合并后的正则表达式，匹配查询参数和路径参数
    # 匹配形式如 ?param1=value1&param2=value2 或 /:param1/value1/:param2/value2
    # 替换函数
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
    with open("tmp.html","r",encoding="utf-8")as f:
        content = f.read()

    parse_links(content,"https://necp-yd03.test.cgbchina.com.cn/assets/js/app-f075b844-835d2378794369d5f62d.js")
    exit()
