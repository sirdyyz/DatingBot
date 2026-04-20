import pika
import time

counter = 0
start_time = time.time()

def callback(ch, method, properties, body):
    global counter, start_time
    counter += 1
    
    if counter % 1000 == 0:
        elapsed = time.time() - start_time
        rate = 1000 / elapsed if elapsed > 0 else 0
        print(rate)
        print(f"реббит обработал {counter} сообщений")
        start_time = time.time()

credentials = pika.PlainCredentials('ksusha', '12345678')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='test_queue')

print("реббит запцщен")
channel.basic_consume(queue='test_queue', on_message_callback=callback, auto_ack=True)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(f"\nреббит успешно обработал {counter}")
    channel.stop_consuming()