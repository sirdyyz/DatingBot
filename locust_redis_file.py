import time
import redis
from locust import User, task, events, constant_throughput

class RedisClient:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=False)

    def publish(self, payload):
        start_time = time.time()
        try:
            self.r.lpush('test_queue', payload)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="REDIS", name="lpush", 
                response_time=total_time, response_length=len(payload)
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="REDIS", name="lpush", 
                response_time=total_time, exception=e
            )

class RedisProducer(User):
    wait_time = constant_throughput(1)
    
    def on_start(self):
        self.client = RedisClient()
        self.payload = b"pu" * 128

    @task
    def send_message(self):
        self.client.publish(self.payload)