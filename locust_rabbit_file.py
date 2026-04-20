from locust import HttpUser, task, constant_throughput

class RabbitHTTPProducer(HttpUser):
    wait_time = constant_throughput(1)
    
    host = "http://localhost:15672"

    def on_start(self):
        self.payload = "pu" * 128
        self.auth = ("ksusha", "12345678")
        
    @task
    def publish_message(self):
        data = {
            "properties": {},
            "routing_key": "test_queue",
            "payload": self.payload,
            "payload_encoding": "string"
        }
        
        self.client.post(
            "/api/exchanges/%2f/amq.default/publish",
            json=data,
            auth=self.auth,
            name="RabbitMQ HTTP Publish"
        )