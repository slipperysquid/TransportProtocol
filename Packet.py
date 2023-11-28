import array
import hashlib
import struct
import socket
class Packet():
    
    def __init__(self,sender_IP,sender_port, dest_IP,dest_port ,sequence, data:bytes,ack, recvw = 8192,syn = False,fin=False): #all inputs are strings
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
        
    def build(self):
        flags = 0
        if self.ack:
            flags |= (1 << 7)
        if self.syn:
            flags |= (1 << 6)
        if self.fin:
            flags |= (1 << 5)

        
        
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
        
        header = struct.pack(
            '!III',
            socket.inet_aton(self.sender_IP),#sender ip
            socket.inet_aton(self.dest_IP),#dest IP
            socket(len(packet) + len(self.data))#length of protocol segment
        )
        
        checksum = self.checksum(header+packet+self.data)
        #putting whole packet together
        packet = header + packet[:16] + struct.pack('H',checksum) + packet[18:]

        return packet

        
    def checksum(packet):
        #padding the packet
        if len(packet) % 2 != 0:
            packet += b'\0'

        #getting the 16 bit ones compliment of a packet
        ones = sum(array.array("H", packet))
        ones = (ones >> 16) + (ones & 0xffff)
        ones += ones >> 16

        return (~ones) & 0xffff

    
