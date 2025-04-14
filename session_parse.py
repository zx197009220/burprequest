## 解析会话
import requests


def getcookie():

    url = "https://mall.cgbchina.com.cn//api/user/web/login/buyer/identify"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Content-Type":"application/json; charset=UTF-8"
    }
    body = {"password":"118e0e64d44b1314dbf7efd6859ff67be94de0fa","identify":"weizy","app":True}
    response = requests.post(url=url,headers=headers,json=body)
    cookie = response.headers.get('Set-Cookie')
    assert "draco_local" in cookie,"未获取到cookie"
    print("已获取最新cookie")
    return cookie



if __name__ == '__main__':
    print(getcookie())
