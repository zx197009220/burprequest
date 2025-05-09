import yaml

# 数据字典
param_data = {"redirectUri":"http://www.baidu.com","webViewUrl":"http://www.baidu.com","itemId": "119100100777004", "userId": "166053", "shopId": "2100191001", "orderId": "40538079003","reverseOrderId":"10535793001","urgeId": "1349044","id":"11","asid":"11","skuOrderId":"1111","code":"11","activityId":"111"}


with open("paramdict.yml", "r", encoding="utf-8") as f:
    param_data = yaml.safe_load(f)
print(param_data)