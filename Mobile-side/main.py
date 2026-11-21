import requests
from sensor_manager import SensorManager
import time

sm = SensorManager(1)
sensor_value=[]
for i in range(8):
    l = sm.poll_event(1000)
    sensor_value.extend(l)
    time.sleep(1)
print(len(sensor_value))


url="http://you_pc_ip:8000/infer/"

r=requests.post(url,json={"data":sensor_value})

if r.status_code==200:
    print(r.json())
else:
    print(f"Error:-{r.status_code}:{r.text}")
