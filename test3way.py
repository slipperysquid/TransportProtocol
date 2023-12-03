
import Receiver
import time
from protocol import Protocol

proto = Protocol('0.0.0.0',5001)
conn = proto.accept(16384)
conn.listen()
data = b''
while True:
    try:
        conn.set_timeout(0.5)
        data += conn.receive_data(8192)
    except:
           break
with open("test2.txt",'wb') as f:
            f.write(data)    

