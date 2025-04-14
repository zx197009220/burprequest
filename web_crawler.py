## 异步爬取api，数据来源于响应包，同时将流量代理到burp suite，方便HaE进行分析
import asyncio
import json
import re
import time
from urllib.parse import urljoin,urlparse
from log import logger
import httpx
from urllib3.util.retry import Retry
from httpx import RemoteProtocolError, ConnectError, ReadTimeout
from link_extractor import parse_links,param_dict
from messageparse import message
from config import crawler_MaxDepth,crawler_Proxies,regex_RemoveUrlContext,crawler_MaxRetries
from session_parse import getcookie



# 去除url上下文
re_remove_url_context = re.compile(r"(https?://[^/]+)/[^/]+(/.*)")
# re_remove_url_context = re.compile(regex_RemoveUrlContext)


url_completed = set()

# crawler_Proxies = None

gic = message()
headers = gic.headers
data = gic.body

async def network_request(request_queue, process_queue,method="get"):

    if method == "get":
        body = None
    else:
        body = data

    timeout_config = httpx.Timeout(
        connect=5.0,  # 连接超时 5s
        read=60.0,  # 读取超时 60s（根据文件大小调整）
        write=10.0,  # 发送超时 10s
        pool=15.0  # 连接池等待 15s
    )
    # 创建一个重试策略
    retries = Retry(
        total=3,  # 最大重试次数
        backoff_factor=1,  # 重试间隔（秒）
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
        allowed_methods=["GET", "POST"],  # 允许重试的 HTTP 方法
    )


    # 防止同时发起过多请求导致服务端压力
    transport = httpx.AsyncHTTPTransport(retries=retries)

    async with httpx.AsyncClient(proxies=crawler_Proxies,headers=headers, timeout=timeout_config,transport=transport, verify=False) as client:
        while True:
            url,urlProperty = await request_queue.get()
            if url is None:
                break  # 接收到 None 作为停止信号
            urlFuzz, depth = urlProperty
            if len(depth.split(".")) > int(crawler_MaxDepth):
                continue
            if url in url_completed:
                request_queue.task_done()
                continue
            url_completed.add(url)
            host = urlparse(url).netloc

            try:
                headers["host"] = host
                response = await client.request(method, url, headers=headers, json=body)

                if urlFuzz == "fuzz" and response.status_code in (404,500):
                    url = re_remove_url_context.sub(r"\1\2", url)
                    response = await client.request(method, url, headers=headers, json=body)

                if 302 == response.status_code:
                    url = response.headers.get("Location")
                    response = await client.request(method, url, headers=headers, json=body)
                # if 200 != response.status_code:
                #     print(f"【{response.status_code}】【{depth}】【{urlFuzz}】: {url}")
                logger.info(f"【{response.status_code}】【{depth}】【{urlFuzz}】: {url}")
                await process_queue.put((response.text,url,depth))  # 存放(url, response_content)
            except RemoteProtocolError as rpe:
                print(f"【服务器协议中断】：{rpe} {url}")  # 如连接被服务器主动关闭
            except ConnectError as ce:
                print(f"【网络层异常】：{ce} {url}")  # 涵盖防火墙、DNS等问题
            except ReadTimeout as ce:

                print(f"【连接层异常】：{ce} {url}")  # 如服务器主动断开、防火墙拦截等（网页6）
            except Exception as e:
                print(f"【其他异常：】【{e}】{url}")
            finally:
                request_queue.task_done()

        await request_queue.put((None, None))


async def content_processor(process_queue, request_queue,event):
    while True:

        response_content,url,depth = await process_queue.get()
        if response_content is None:
            break  # 接收到 None 作为停止信号
        new_urls = await parse_links(response_content, url, depth)
        event.set()
        for new_url,urlProperty in new_urls.items():
            await request_queue.put((new_url,urlProperty))  # 将新 URL 放回网络请求队列
        process_queue.task_done()

    await process_queue.put((None, None, None))

async def monitor_queues(process_queue, request_queue,event):
    await event.wait()
    while True:
        if request_queue.empty() and process_queue.empty():
            empty_checks = 3
            while empty_checks:
                await asyncio.sleep(4)
                if request_queue.empty() and process_queue.empty():
                    empty_checks-=1
                else:
                    break
            if empty_checks == 0:
                await request_queue.put((None, None))
                await process_queue.put((None, None, None))
                print("Both queues are empty. Ending tasks.")
                break

        await asyncio.sleep(1)  # 短暂休眠后再次检查

async def main(start_url,method):
    request_queue = asyncio.Queue()
    process_queue = asyncio.Queue()

    # 初始化队列和任务
    if isinstance(start_url,str):
        await request_queue.put((start_url,("source","1")))

    if isinstance(start_url,list):
        depth = 0
        for url in start_url:
            depth +=1
            await request_queue.put((url,("source",f"{depth}")))

    event = asyncio.Event()

    # 创建生产者任务
    producer_task = [asyncio.create_task(network_request(request_queue, process_queue,method)) for _ in range(5)]

    # 创建消费者任务
    consumer_task = [asyncio.create_task(content_processor(process_queue, request_queue,event))for _ in range(3)]

    # 队列监控线程
    monitor = asyncio.create_task(monitor_queues(process_queue, request_queue,event))
    await asyncio.gather(*producer_task,*consumer_task,monitor)

    monitor.cancel()

def getstarturls(start_file,context=""):

    start_url = []
    domain = "https://gic.test.cgbchina.com.cn:1443"

    with open(start_file, "r", encoding='utf-8')as file:
        for line in file.readlines():
            line = line.rstrip('\n')
            if line.startswith("http"):
                start_url.append(line)
            else:
                line = context+"/"+line
                url = line.replace("//","/")
                start_url.append(urljoin(domain, url))
    return start_url


# 运行主函数
if __name__ == '__main__':
    start_url = 'https://mall.cgbchina.com.cn'


    start_url = getstarturls("start.txt",context = "")

    asyncio.run(main(start_url,"GET"))
    print(len(url_completed))

