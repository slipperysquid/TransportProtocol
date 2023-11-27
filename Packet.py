import hashlib

class Packet():

    def __init__(self,sender_IP,sender_port, dest_IP,dest_port ,sequence, num_connections,recv_window, data): #all inputs are strings
        self.packet = {
            'senderIP':sender_IP,
            'senderPort':int(sender_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'dest_IP':dest_IP,
            'dest_port':int(dest_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'sequence': int(sequence).to_bytes(4,byteorder='little',signed=False),#32 bit
            'checksum': data.encode().digest(),#checksum generated (128 bit)
            'num_connections':int(num_connections).to_bytes(2,byteorder='little',signed=False),
            'recv_window':recv_window,
            'data':data.encode()
        }