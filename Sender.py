
import array
import Packet 
import socket
import hashlib
import struct
from helpers import make_threaded
import time

globals()['ack_received'] = False
class Sender():

    def __init__(self,sender_IP,sender_port):
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        self.send_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.dest_IP = None
        self.dest_port = None
        self.windowsize = 1
        self.recv_socket.bind((self.sender_IP,self.sender_port))
    
    #do a 3 way handshake
    def get_connection(self, dest_IP, dest_port):
        self.dest_IP = dest_IP
        self.dest_port = dest_port
        connected = False
        while not(connected):
            #create the initial packet (in our protocol the first packet of handshake has seq 0)
            initial_packet = Packet.Packet(self.sender_IP,self.sender_port, self.dest_IP,self.dest_port ,sequence=0, data=None,ack=0,syn=True).build()
            
            #reach out to server
            self.send_socket.sendto(initial_packet,(self.dest_IP,self.dest_port))
            #wait for an ack
            try:
                self.recv_socket.settimeout(0.3)
                data, addr = self.recv_socket.recvfrom(32)
                ack_data = struct.unpack('!4s4sIHHIIHHHxx',data)
                flags = ack_data[7]
                ack_num = ack_data[6]
                sequence_num = ack_data[5]
                checksum = ack_data[9]
                if (self.validate_packet(data,checksum) == False):#check valid
                    print("Threeway handshake failed: Received a syn packet! but bad checksum! RESTARTING")
                elif (not(flags & (1 << 7))):#check ack
                    print("Threeway handshake failed:or the packet received is not an ack! RESTARTING")
                elif not(flags & (1 << 6)):#check syn
                        print("Three way handshake failed:  ack received is not a syn ack")     
                        
                elif ack_num != 1:#check ack = seq + 1
                        print("Three way handshake failed:  ack number received does not match ack number expected")
                        
                else:

                    #building last ack 
                    last_packet = Packet.Packet(self.sender_IP,self.sender_port, self.dest_IP,self.dest_port ,sequence=1, data=None,ack=sequence_num+1,is_ack=True).build()
                    #send the last ack
                    self.send_socket.sendto(last_packet,(self.dest_IP,self.dest_port))

                    print("3 WAY HANDSHAKE ESTABLISHED") 
                    connected = True
            
            except Exception as e:
                print("Three way handshake failed: {}".format(e))
        return connected
            
    
    
    def send_data(self,data):
        #split data into chunks
        chunks = []
        while len(data) >= 1024:
           chunks.append(data[0:1024]) 
           data = data[1024:]
        if len(data) > 0:
            chunks.append(data)
        #begin GBN
        window_base = 0
        N = 54
        next_seq_num = 0
        timer_started = False
        while True:
            #start the ack listening thread
            globals()['close_ack_thread'] = False
            #ack_data = self.listen_for_ack()
        
            #if the sequence number is within the window, send a packet
            if(next_seq_num == len(chunks)):
                break
            while (next_seq_num < window_base + N):
                print("sending packet with sequence number {}".format(next_seq_num))
                packet = Packet.Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                self.send_socket.sendto(packet,(self.dest_IP,self.dest_port))  
                #start timer after sending packing if the sequence number is the window base
                if (window_base == next_seq_num):
                    start_time = time.time()
                    timer_started = True
                next_seq_num += 1
            try:
                self.recv_socket.settimeout(0.3)
                ack_data,addr = self.recv_socket.recvfrom(32)
                print("ack received")
                ack = struct.unpack('!4s4sIHHIIHHHxx',ack_data)
                flags = ack[7]
                ack_num = ack[6]
                checksum = ack[9]
                #validate the ack
                if (self.validate_packet(ack_data,checksum) == False):#check valid
                    print("Ack received is not valid")
                elif (not(flags & (1 << 7))):#check ack
                    print("Packet received is not an ack")
                elif (ack_num == window_base):
                    window_base += 1
                    print("inscreased window base")
                    if window_base == next_seq_num:
                        timer_started = False
                    else:
                        start_time = time.time()
                        timer_started = True
            except socket.timeout:
                print("packet time out")
                start_time = time.time()
                timer_started = True
                for i in range(window_base,next_seq_num - 1):
                    packet = Packet.Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                    self.send_socket.sendto(packet,(self.dest_IP,self.dest_port))
            
            globals()['close_ack_thread'] = True
            

        globals()['close_ack_thread'] = True
        print("Done sending, closing connection")
        close_pack = Packet.Packet(self.sender_IP,self.sender_port, self.dest_IP,self.dest_port ,sequence=0, data=None,ack=0,fin=True).build()
        self.send_socket.sendto(close_pack,(self.dest_IP,self.dest_port))
        self.recv_socket.settimeout(0.3)
        data, addr = self.recv_socket.recvfrom(32)
        if (self.validate_packet(data,checksum) == False):#check valid
            print("closure failed: bad checksum! ")
        elif (not(flags & (1 << 7))):#check ack
            print("closure failed:or the packet received is not an ack! ")
        elif not(flags & (1 << 5)):#check syn
            print("closure failed:  ack received is not a fin ack")



        print("done closing")
        



    @make_threaded
    def listen_for_ack(self):
        #wait for an ack
        while not(globals()['close_ack_thread']):
            self.recv_socket.settimeout(0.2)
            try:
                data, addr = self.recv_socket.recv(32)
                print("Thread received packet")
                globals()['ack_received'] = True
                return data
            except Exception as e:
                #print(e)
                continue


        
        '''''''''
        #create packets to send
        while (next_seq_num < window_base + N):
            packet = Packet.build(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 )
            sndpkt.append(packet)
            next_seq_num +=1

        #send packets
        #start timer
        for packet in sndpkt:
            self.send_socket.sendto(packet,(self.dest_IP,self.dest_port))   
        #wait for acks
        while timer != 0:
            get acks
        #update window size N based on loss or # of acks received also move window_base up  
        #loop'''

        
        
    '''def receive_ack(self,timeout):
        self.recv_socket.settimeout(timeout)
        try:
            #receive header from buffer
            data, addr = self.recv_socket.recvfrom(32)

            sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx",data)
            #no need to receive data cause it's an ack
            #check checksum
            if self.validate_packet(data,checksum=checksum) == False:
                raise ValueError('The ack failed the checksum test')
            if flags & (1 << 7):
                raise Exception('the packet received is not an ACK')
                
            return (sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw)
        except TimeoutError as e:
            raise TimeoutError('TIMEOUT:did not receive ack in time')
    '''

    def validate_packet(self,packet,checksum):
        zero = 0
        packet = packet[:28] + zero.to_bytes(2,byteorder='big') + packet[30:]
        #padding the packet
        if len(packet) % 2 != 0:
            packet += b'\0'

        #getting the 16 bit ones compliment of a packet
        ones = array.array("H", packet)
        ones = sum(ones)
        ones = (ones >> 16) + (ones & 0xffff)
        ones += ones >> 16
        compliment = (~ones) & 0xffff
        return checksum == compliment
