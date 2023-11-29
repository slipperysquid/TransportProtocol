import socket
import struct
import Packet
import array

class Receiver():

    def __init__(self,recv_IP,recv_port):
        self.sender_IP = None
        self.sender_port = None
        self.send_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.recv_IP = recv_IP
        self.recv_port = recv_port
        pass
    

    def listen_for_connection(self):
        connected= False
        self.recv_socket.bind((self.recv_IP,self.recv_port))
        while not(connected):
            #receive a syn packet
            data,addr = self.recv_socket.recvfrom(32)
            sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx",data)
            #check checksum, check for syn bit
            if (self.validate_packet(data,checksum) == False):
                print("Threeway handshake failed: Received a syn packet! but bad checksum! RESTARTING")
            elif (not(flags & (1 << 6))):
                
                print("Threeway handshake failed:or the packet received is not a syn! RESTARTING")
            else:
                #create synack
                synack=Packet.Packet(sender_IP=self.recv_IP,sender_port=self.recv_port, dest_IP=socket.inet_ntoa(sender),dest_port=sender_port ,sequence=0, data=None,ack=1,syn=True,is_ack=True).build()
                #send synack
                self.send_socket.sendto(synack,(socket.inet_ntoa(sender),sender_port))

                #receive last ack of the three way handshake
                data,addr = self.recv_socket.recvfrom(32)
                sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx",data)
                #check checksum
                if self.validate_packet(data,checksum) == False:
                    print("Threeway handshake failed: Received a syn packet! but bad checksum!RESTARTING")
                #check for ack bit
                elif not(flags & (1 << 7)):
                    print('Threeway handshake failed: the last packet received is not an ack! RESTARTING')
                else:
                    print("threeway established")
                    self.sender_IP = sender
                    self.sender_port = sender_port
                    connected = True
        return connected
    
    def validate_packet(self,packet:bytes,checksum:bytes):
        packet = packet[:28] + struct.pack('H',0) + packet[30:]
       
        #padding the packet
        if len(packet) % 2 != 0:
            packet += b'\0'

        #getting the 16 bit ones compliment of a packet
        ones = (array.array("H", packet))
        ones = (sum(ones))
        ones = (ones >> 16) + (ones & 0xffff)
        ones += ones >> 16
        compliment = (~ones) & 0xffff

        return checksum == compliment

    def receive_packet(self):

        prev_seq = 0
        recieve = True
        output = []
        while recieve:
            header,addr = self.recv_socket.recvfrom(1056)
            sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx", header[:32])
            print("recv seq = ", sequence)
            if flags and (1 << 5):
                
                ack = Packet.Packet(sender_IP=self.recv_IP, 
                                        sender_port=self.recv_port, 
                                        dest_IP=socket.inet_ntoa(sender), 
                                        dest_port=sender_port ,sequence=1, 
                                        data=None, 
                                        ack=sequence+1,
                                        fin=True, is_ack=True).build()
                self.send_socket.sendto(ack, (socket.inet_ntoa(sender),sender_port))
                recieve = False
                

            #check corruption
            if self.validate_packet(header, checksum) and sequence == prev_seq:
                print("validated packet we seq ", sequence)
                ack = Packet.Packet(sender_IP=self.recv_IP, 
                                    sender_port=self.recv_port, 
                                    dest_IP=socket.inet_ntoa(sender), 
                                    dest_port=sender_port ,sequence=prev_seq, 
                                    data=None, 
                                    ack=prev_seq,
                                    syn=False,is_ack=True).build()
                prev_seq += 1
                print(struct.unpack("!4s4sIHHIIHHHxx",ack))
                self.send_socket.sendto(ack, (socket.inet_ntoa(sender),sender_port))
                #read the data from the buffer
                data_chunk = header[32:]
                print("received data: {}".format(data_chunk))
                print("sent ack, data chunk - ", data_chunk)
                output.append(data_chunk)
                
            else:
                #send previous ack
                ack = Packet.Packet(sender_IP=self.recv_IP, 
                                    sender_port=self.recv_port, 
                                    dest_IP=socket.inet_ntoa(sender), 
                                    dest_port=sender_port ,sequence=prev_seq, 
                                    data=None, 
                                    ack=prev_seq,
                                    syn=False,is_ack=True).build()
                
                self.send_socket.sendto(ack, (socket.inet_ntoa(sender),sender_port))

        print("we received this: {}".format(output))
        return b''.join(output)

 
    
    #recv 32
    #read header that u got for length of packet
    #recv length - 32 -> gives data