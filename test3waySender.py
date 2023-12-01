import Sender
import time
from protocol import Protocol

'''
send = Sender.Sender('127.0.0.1',5001)

send.get_connection('127.0.0.1', 5000)
data = """ """
with open("stuff.txt") as f:
    start = time.time()
    send.send_data(f.read().encode())
    end = time.time()

print(end - start)
'''
proto = Protocol('127.0.0.1',9999)
conn = proto.conn(dest_IP='127.0.0.1',dest_port=5000)


with open("stuff.txt") as f:
    start = time.time()
    conn.send_data(f.read().encode())
    end = time.time()
data = conn.receive_data()
#print(data)