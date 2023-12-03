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
proto = Protocol('66.183.48.44',9999)
conn = proto.conn(dest_IP='185.77.96.12',dest_port=5001)


with open("book.txt",encoding="utf8") as f:
    start = time.time()
    conn.send_data(f.read().encode())
    end = time.time()
print("finished in {}".format(end - start))
conn.close()