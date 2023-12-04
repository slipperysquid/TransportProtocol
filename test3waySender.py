
from protocol import Protocol
#put public ip here or put local ip if testing on local network
proto = Protocol('',9999)
#put target ip and port here
conn = proto.conn(dest_IP='',dest_port=5001)

with open("book.txt",encoding="utf8") as f:
    conn.send_data(f.read().encode())
    

conn.close()