import redis
from PyQt5.QtCore import QThread, pyqtSignal


class RedisSubscriber(QThread):
    new_channel = pyqtSignal(str)

    def __init__(self, redis_url, channel_pattern):
        super().__init__()
        self.redis_url = redis_url
        self.channel_pattern = channel_pattern

    def run(self):
        r = redis.Redis.from_url(self.redis_url)
        pubsub = r.pubsub()
        pubsub.psubscribe(self.channel_pattern)
        for message in pubsub.listen():
            if message["type"] == "pmessage":
                self.new_channel.emit(message["channel"].decode("utf-8"))
