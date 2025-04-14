## 解析burpsuite 中导出的xml，去重后生成xlsx。记录url的签名，去重后保存到config.json中，并生成去重后的xml，方便再次解析成xlsx。
import base64
import hashlib
import os
import re
import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import json
import urllib3
import asyncio
import httpx
from urllib3.exceptions import InsecureRequestWarning
import pandas as pd
from messageparse import message as msg
from session_parse import getcookie
import openpyxl

urllib3.disable_warnings(category=InsecureRequestWarning)

# 正则替换报文会话信息
regex = "authorization:.*"
replace = "authorization: eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxODkxMTQ0NzQwNiIsInVzZXJJZCI6IjM0OTMwMzQ2NDE5OTM4MDkwMTAiLCJuYW1lIjoi6YCg5pWw5qyj56CU54u8MSIsImV4cCI6MTcyMjU5Mzk2M30.JUx_KmFS6z-9TJpQ1Y81MN-jibKFAjrQO_qMUH3Rj1BpRvbmKiCWJP8FLrxQwJjjjuxoeyivgNUPKPySPiR9RanpHtnY8Pb0RFRi4z_N6Ysr07_rgBEY7pr3mWvgDrmcV6SN1IdqhJw3WHFd7Z9-MteZEJUrbK1DBgprF5GlxVQ"
matchandreplace = {regex:replace}

class playback:

    request = ""
    url = ""
    method = ""

    def __init__(self,burppath=None):
        if burppath:
            self.messageunique(burppath)
        self.semaphore = asyncio.Semaphore(10)
        # self.cookie = getcookie()

    def parsemessageinfo(self,message,request_or_response):
        messagetext = message.find(request_or_response).text
        if messagetext is None:
            return None, None
        messageinfo = base64.b64decode(messagetext).decode("utf-8", errors='replace')

        # 替换会话的正则matchandreplace
        res = msg(messageinfo,matchandreplace)

        return res.headers,res.body
    def parsemessage(self,message):
        self.url = message.find("url").text
        self.status = message.find("status").text
        self.comment = message.find("comment").text
        self.extension = message.find("extension").text
        parseurlresult = urlparse(self.url)
        self.path = parseurlresult.path
        self.method = message.find("method").text
        self.reqheaders,self.reqbody = self.parsemessageinfo(message,"request")
        self.resheaders,self.resbody = self.parsemessageinfo(message,"response")
        self.req_content_length =self.reqheaders["Content-Length"] if "Content-Length" in self.reqheaders else None
        if self.resheaders:
            self.res_content_length =self.resheaders["Content-Length"] if "Content-Length" in self.resheaders else "0"


    def excelbyburp(self,filepath=None):

        assert os.path.exists(filepath),"[error]:56 "+filepath+"文件不存在"
        input_root = ET.parse(filepath).getroot()
        xlsx_data = {}
        for burp_msg in input_root:
            self.parsemessage(burp_msg)
            xlsx_data.setdefault("method", []).append(self.method)
            xlsx_data.setdefault("url", []).append(self.url)
            xlsx_data.setdefault("path", []).append(self.path)
            xlsx_data.setdefault("status", []).append(self.status)
            xlsx_data.setdefault("comment", []).append(self.comment)
            xlsx_data.setdefault("res_content_length", []).append(self.res_content_length)

        df_data = pd.DataFrame(xlsx_data)
        xlsxpath = filepath.rsplit(".",1)[0]+".xlsx"
        df_data.to_excel(xlsxpath,index=False)
        self.compareinterface(xlsxpath)

    def compareinterface(self,appxlsxpath):

        all_interface_path = "all_interface.xlsx"

        df_sheet1 = pd.read_excel(appxlsxpath, sheet_name='Sheet1')

        all_sheet1 = pd.read_excel(all_interface_path, sheet_name='Sheet1')

        df_sheet1['info'] = ""
        all_sheet1['math'] = False

        for index2, row2 in all_sheet1.iterrows():
            for index1, row1 in df_sheet1.iterrows():
                if row2["path"].strip() in row1["path"]:
                    all_sheet1.at[index2, 'math'] = True
                    df_sheet1.at[index1, 'info'] = row2['info']

        with pd.ExcelWriter(appxlsxpath, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:
            all_sheet1.to_excel(writer, sheet_name="Sheet2", startrow=0, startcol=0, index=False, header=True)
            df_sheet1.to_excel(writer, sheet_name="Sheet1", startrow=0, startcol=0, index=False, header=True)
        pass

    def signatureconfig(self,path):

        jsonpath = path.rsplit('.')[0]+".json"
        if os.path.exists(jsonpath):
            with open(jsonpath,"r",encoding="utf-8")as file:
                signature = json.load(file)
        else:
            signature = {}
            with open(jsonpath, 'w') as file:
                json.dump({}, file)
        return signature,jsonpath

    def getxmlpath(self,path):
        assert os.path.exists(path), path + "文件不存在"

        input_file = os.path.abspath(path)
        parts = input_file.rsplit('.')
        dirpath = parts[0]
        # extension = parts[1] if len(parts) > 1 else None

        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        output_time_file = dirpath + "/" + datetime.datetime.now().strftime('%Y%m%d%H%M') + ".xml"
        output_all_file = dirpath + "/" + os.path.basename(dirpath) + ".xml"

        return input_file,output_time_file,output_all_file

    def messageunique(self,filename):

        input_file_name,output_time_name,output_all_name = self.getxmlpath(filename)

        input_root = ET.parse(input_file_name).getroot()
        output_time_root = ET.parse(output_time_name).getroot() if os.path.exists(output_time_name) else ET.Element(input_root.tag)
        output_all_root = ET.parse(output_all_name).getroot() if os.path.exists(output_all_name) else ET.Element(input_root.tag)
        signature_temp_time = set()
        signature_all_time,json_path = self.signatureconfig(output_all_name)

        for burp_msg in input_root:
            self.parsemessage(burp_msg)
            sign_text = self.path + str(self.req_content_length)
            digest = self.calculate_md5_string(sign_text)
            if digest not in signature_temp_time:
                signature_temp_time.add(digest)
                output_time_root.append(burp_msg)
            else:
                continue

            if digest not in signature_all_time:
                signature_all_time[digest] = self.url
                output_all_root.append(burp_msg)
            else:
                continue

        tree = ET.ElementTree(output_time_root)
        tree.write(output_time_name, encoding='utf-8', xml_declaration=True)

        tree = ET.ElementTree(output_all_root)
        tree.write(output_all_name, encoding='utf-8', xml_declaration=True)

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(signature_all_time, json_file, ensure_ascii=False, indent=4)

        self.excelbyburp(output_all_name)

    async def send_requests(self,xmlfile):

        assert os.path.exists(xmlfile),xmlfile+"文件不存在"
        # 解析XML文件
        tree = ET.parse(xmlfile)
        input_root = tree.getroot()

        tasks = []

        for message in input_root:

            self.parsemessage(message)

            # 如果存在Content-Length，则删除它
            if "Content-Length" in self.reqheaders:
                del self.reqheaders["Content-Length"]
            task = asyncio.create_task(self.fetch_with_proxy(self.method, self.url, self.reqheaders, self.reqbody))
            tasks.append(task)
        await asyncio.gather(*tasks)



    async def fetch_with_proxy(self,method, url, headers, data, proxies={"http://": "http://127.0.0.1:9091","https://": "http://127.0.0.1:9091",}):
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(verify=False, timeout=None,proxies=proxies) as client:
                    response = await client.request(method, url, headers=headers, json=data)
                    print(response)
                    return response
                    response.raise_for_status()  # 如果状态码是4xx或5xx，将抛出HTTPStatusError
                    return response
            except httpx.HTTPStatusError as exc:
                # exc.response 就是包含400响应的response对象
                if exc.response.status_code == 400:
                    print("Received a 400 Bad Request response")
                    # 处理400响应，例如：
                    return exc.response  # 返回response对象
                else:
                    # 处理其他4xx响应
                    print(f"Received an HTTP error: {exc.response.status_code}")
                    return exc.response
            except Exception as e:
                # 处理其他类型的异常
                print(f"An unexpected error occurred: {e}")
                return None



    def calculate_md5_string(self,input_string):

        input_bytes = input_string.encode('utf-8')

        md5_hash = hashlib.md5()

        md5_hash.update(input_bytes)

        return md5_hash.hexdigest()

async def main(xmlfile):
    pb = playback()
    await pb.send_requests(xmlfile)


if __name__ == '__main__':

    burppath =  "gic.burp"
    # burppath =  "./gic/gic.xml"

    pb = playback(burppath)


    # pb.excelbyburp(xmlpath)
    # asyncio.run(main(r"D:\poc\python\burprequest\gic\gic.xml"))