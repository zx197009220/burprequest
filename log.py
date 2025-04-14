import logging

# 创建主日志对象
logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)

# 配置文件处理器（显示时间）
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m-%d %H:%M')
file_handler.setFormatter(file_formatter)

# 配置控制台处理器（不显示时间）
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

if __name__ == '__main__':
    # 使用示例
    logger.info("用户登录成功")
    logger.error("文件读取失败")
