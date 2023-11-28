import hashlib

class Packet():
    
    def __init__(self,sender_IP,sender_port, dest_IP,dest_port ,sequence, data): #all inputs are strings
        self.packet = {
            'senderIP': [int(number).to_bytes(1,byteorder='little',signed=False) for number in sender_IP.split('.') ],
            'senderPort':int(sender_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'dest_IP':[int(number).to_bytes(1,byteorder='little',signed=False) for number in dest_IP.split('.') ],
            'dest_port':int(dest_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'sequence': str(int(sequence).to_bytes(4,byteorder='little',signed=False)),#32 bit
            'checksum': self.checksum(),#checksum generated (128 bit)
            'data':data.encode()
        }
        
    def checksum(self):
        bytestring = + self.packet['senderPort'] + self.packet['dest_post']+ self.packet['sequence'] + self.packet['data']
        for num in self.packet['senderIP']:
            bytestring += num
        for num in self.packet['dest_IP']:
            bytestring += num

        return bytestring.digest()


    

class Ack():
    def __init__(self,sender_IP,sender_port, dest_IP,dest_port,sequence,num_connections,recv_window):
        self.ack = {
            'senderIP':[int(number).to_bytes(1,byteorder='little',signed=False) for number in sender_IP.split('.') ],
            'senderPort':int(sender_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'dest_IP':[int(number).to_bytes(1,byteorder='little',signed=False) for number in dest_IP.split('.') ],
            'dest_port':int(dest_port).to_bytes(2,byteorder='little',signed=False),#16 bit
            'sequence': int(sequence).to_bytes(4,byteorder='little',signed=False),#32 bit
            'recv_window':int(recv_window).to_bytes(2,byteorder='little',signed=False),
            'checksum':self.checksum()
        }
    
    def checksum(self):
        bytestring = + self.packet['senderPort'] + self.packet['dest_post']+ self.packet['sequence'] + self.packet['recv_window']
        for num in self.packet['senderIP']:
            bytestring += num
        for num in self.packet['dest_IP']:
            bytestring += num

        return bytestring.digest()
