
from protocol import Protocol

proto = Protocol('66.183.48.44',9999)
conn = proto.conn(dest_IP='185.77.96.12',dest_port=5001)

with open("book.txt",encoding="utf8") as f:
    conn.send_data(f.read().encode())
    

conn.close()