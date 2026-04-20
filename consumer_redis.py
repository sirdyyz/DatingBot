import redis
import time

r = redis.Redis(host='localhost', port=6379)
print("редис запущен")

counter = 0
start_time = time.time()

try:
    while True:
        msg = r.brpop('test_queue', timeout=1)
        
        if msg:
            counter += 1
            if counter % 1000 == 0:
                elapsed = time.time() - start_time
                rate = 1000 / elapsed if elapsed > 0 else 0
                print(rate)
                print(f"редис обработал {counter} сообщений")
                start_time = time.time()
                
except KeyboardInterrupt:
    print(f"\nредис успешно обработал {counter}")