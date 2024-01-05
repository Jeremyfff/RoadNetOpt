import logging

class MergeFilter(logging.Filter):
    def __init__(self):
        self.last_record = None
        self.count = 0

    def filter(self, record):
        if record.msg == self.last_record:
            self.count += 1
            return False
        else:
            if self.last_record is not None:
                record.msg = f"{self.last_record} (Repeated {self.count} times)"
                self.count = 0
            self.last_record = record.msg
            return True

# 创建 logger 对象
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建自定义过滤器
merge_filter = MergeFilter()

# 将过滤器添加到 logger 对象
logger.addFilter(merge_filter)

# 输出相同信息多次
logger.info("Hello")
logger.info("Hello")
logger.info("Hello")
logger.info("World")
logger.info("World")

# 移除过滤器
logger.removeFilter(merge_filter)