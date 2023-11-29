import array
import hashlib
import struct
import socket

class Packet():
    
    def __init__(self,sender_IP,sender_port, dest_IP,dest_port ,sequence, data:bytes,ack, recvw = 8192,syn = False,fin=False,is_ack=False): #all inputs are strings
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        self.dest_IP =dest_IP
        self.dest_port =dest_port
        self.sequence = sequence
        self.ack = ack
        self.data = data
        self.recvw = 8192
        self.syn = syn
        self.fin = fin
        self.is_ack = is_ack
        
    def build(self):
        flags = 0
        if self.is_ack:
            flags |= (1 << 7)
        if self.syn:
            flags |= (1 << 6)
        if self.fin:
            flags |= (1 << 5)

        
        #H=unsigned 2 byte int , I = unsigned 4 byte int, x = padding byte
        packet = struct.pack(
            '!HHIIHHHxx',
            self.sender_port, #source port
            self.dest_port, #destination port
            self.sequence, #sequence number
            self.ack, #acknowledge number
            flags, # ack, syn , fin bits followed by 00000
            self.recvw, #receive window
            0, #initial checksum is 0
        )
        if self.data:
            length = len(packet) + len(self.data)
        else:
            length = len(packet)

        header = struct.pack(
            '!4s4sI',
            socket.inet_aton(self.sender_IP),#sender ip
            socket.inet_aton(self.dest_IP),#dest IP
            length#length of protocol segment
            
        )

        #calc checksum
        if self.data:
            checksum = self.checksum((header+packet+self.data))
            packet = header + packet[:16] + checksum.to_bytes(2,byteorder='big') + packet[18:] + self.data
        else:
            checksum = self.checksum((header+packet))
            packet = header + packet[:16] + checksum.to_bytes(2,byteorder='big') + packet[18:] 
        #putting whole packet together
        

        return packet
        
    def checksum(self,packet):
        #padding the packet
        if len(packet) % 2 != 0:
            packet += b'\0'

        #getting the 16 bit ones compliment of a packet
        ones = array.array("H", packet)
        ones = sum(ones)
        ones = (ones >> 16) + (ones & 0xffff)
        ones += ones >> 16
        compliment = (~ones) & 0xffff
       
        return compliment

    
