import socket
from Packet import Packet
import struct
from Connection import Connection

class Protocol():

    def __init__(self,IP,port):
        self.IP = IP
        self.port = port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.dest_max_window_size = None
        if (IP == '0.0.0.0' or IP == '127.0.0.1' or IP == 'localhost'):
            self.socket.bind((self.IP,self.port))
            s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(('192.255.255.255', 1))
            self.IP = s.getsockname()[0]
            print('IP = {}'.format(self.IP))
        else:
            self.socket.bind(('0.0.0.0',self.port))

    def conn(self,dest_IP,dest_port,max_window_size = 4096):
        connected = False
        while not(connected):
            #create the initial packet (in our protocol the first packet of handshake has seq 0)
            initial_packet = Packet(self.IP,self.port, dest_IP,dest_port ,sequence=0,recvw=max_window_size, data=None,ack=0,syn=True).build()
            
            #reach out to server
            self.socket.sendto(initial_packet,(dest_IP,dest_port))
            #wait for an ack
            try:
                self.socket.settimeout(0.3)
                data, addr = self.socket.recvfrom(32)
                ack_data = struct.unpack('!4s4sIHHIIHHHxx',data)
                flags = ack_data[7]
                ack_num = ack_data[6]
                self.dest_max_window_size = [8]
                sequence_num = ack_data[5]
                checksum = ack_data[9]
                if (Packet.validate_packet(packet=data,checksum=checksum) == False):#check valid
                    print("Threeway handshake failed: Received a syn packet! but bad checksum! RESTARTING")
                elif (not(flags & (1 << 7))):#check ack
                    print("Threeway handshake failed: the packet received is not an ack! RESTARTING")
                elif not(flags & (1 << 6)):#check syn
                        print("Three way handshake failed:  ack received is not a syn ack")     
                        
                elif ack_num != 1:#check ack = seq + 1
                        print("Three way handshake failed:  ack number received does not match ack number expected")
                        
                else:

                    #building last ack 
                    last_packet = Packet(self.IP,self.port, dest_IP,dest_port ,sequence=1, data=None,ack=sequence_num+1,is_ack=True).build()
                    #send the last ack
                    self.socket.sendto(last_packet,(dest_IP,dest_port))

                    print("3 WAY HANDSHAKE ESTABLISHED") 
                    connected = True
            
            except Exception as e:
                print("Three way handshake failed: {}".format(e))
        return Connection(self.IP,self.port,dest_IP,dest_port,self.socket,self.dest_max_window_size)
    

    def accept(self,max_window_size = 4096):
        connected= False
        while not(connected):
            #receive a syn packet
            data,addr = self.socket.recvfrom(32)
            sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx",data)
            self.dest_max_window_size = recw
            #check checksum, check for syn bit
            if (Packet.validate_packet(packet=data,checksum=checksum) == False):
                print("Threeway handshake failed: Received a syn packet! but bad checksum! RESTARTING")
            elif (not(flags & (1 << 6))):
                
                print("Threeway handshake failed:the packet received is not a syn! RESTARTING")
            else:
                #create synack
                synack=Packet(sender_IP=self.IP,sender_port=self.port,recvw=max_window_size, dest_IP=socket.inet_ntoa(sender),dest_port=sender_port ,sequence=0, data=None,ack=1,syn=True,is_ack=True).build()
                #send synack
                self.socket.sendto(synack,(socket.inet_ntoa(sender),sender_port))
                print("sending ack")
                #receive last ack of the three way handshake
                data,addr = self.socket.recvfrom(32)
                sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx",data)
                #check checksum
                if Packet.validate_packet(packet=data,checksum=checksum) == False:
                    print("Threeway handshake failed: Received a syn packet! but bad checksum!RESTARTING")
                #check for ack bit
                elif not(flags & (1 << 7)):
                    print('Threeway handshake failed: the last packet received is not an ack! RESTARTING')
                else:
                    print("threeway established")
                    connected = True
        return Connection(self.IP,self.port, socket.inet_ntoa(sender),sender_port,self.socket,self.dest_max_window_size)