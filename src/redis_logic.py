import redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)

from PyQt5.QtCore import QThread, pyqtSignal


class RedisSubscriber(QThread):
    new_channel = pyqtSignal(str, str, str)  # Emit both channel name and data


    def __init__(self, redis_url, channel_pattern):
        super().__init__()
        self.redis_url = redis_url
        self.channel_pattern = channel_pattern

    def run(self):
        while True:
            try:
                r = redis.Redis.from_url(self.redis_url)
                pubsub = r.pubsub()
                pubsub.psubscribe(self.channel_pattern)
                for message in pubsub.listen():
                    if message["type"] == "pmessage":
                        channel = message["channel"].decode("utf-8")
                        data = message["data"].decode("utf-8")
                        self.new_channel.emit(channel, data, "success")
            except (RedisTimeoutError, RedisConnectionError):
                print("wait for connection")
                self.new_channel.emit("", "", "Wait For Connection ...")

