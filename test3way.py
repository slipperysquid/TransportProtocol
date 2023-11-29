
import Receiver
import time

rec = Receiver.Receiver('127.0.0.1',5000)


rec.listen_for_connection()
data = rec.receive_packet()

with open("test.txt",'wb') as f:
    f.write(data)