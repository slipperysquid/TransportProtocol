import socket
from Packet import Packet
import struct
import threading
import time
from GBN_send import sender
import random
from math import floor
import queue
from helpers import make_threaded
from Timer import Timer
class Connection():
    
    def __init__(self,sender_IP,sender_port,dest_IP,dest_port,sockets:socket.socket, dest_max_window_size, max_window_size):
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        self.socket = sockets
        self.dest_IP = dest_IP
        self.dest_port = dest_port
        self.buffer = []
        self.windowsize = 1
        self.dest_max_window_size = dest_max_window_size
        self.max_window_size = max_window_size
        self.lock = threading.Lock()
        self.closed = False
        self.GBN_sender = sender(self.socket, self.sender_IP,self.sender_port,self.dest_IP,self.dest_port)
        self.listening = False
        self.sending = False
        self.recv_timeout = 0.3
        if max_window_size != 0:
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,max_window_size + 32 * floor(max_window_size/1024))

    def send_data(self,data):
        if self.closed == False:
            if self.listening:
                print("cannot send and listen on same socket")
            else:
                self.sending = True
                self.GBN_sender.send_data(data, self.dest_max_window_size)
                self.sending = False
        else:
            print("cannot send data, connection is closed")


    @make_threaded
    def listen(self):
        if not(self.sending):
            if self.closed == False:
                self.listening = True
                expected_seq = 0
                recieve = True
                output = []
                while recieve:
                
                    try:
                        self.socket.settimeout(75)
                        header,addr = self.socket.recvfrom(1056)
                        sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx", header[:32])
                        
                        if (flags & (1 << 5)):
                            print('fin received')
                            self.lock.acquire()
                            ack = Packet(sender_IP=self.sender_IP, 
                                                    sender_port=self.sender_port, 
                                                    dest_IP=socket.inet_ntoa(sender), 
                                                    dest_port=sender_port ,sequence=1, 
                                                    data=None, 
                                                    ack=sequence+1,
                                                    fin=True, is_ack=True).build()
                            self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                            recieve = False
                            self.lock.release()
                            

                        #check corruption
                        elif Packet.validate_packet(packet=header, checksum=checksum):
                            print("validated packet with sequence number ", sequence)
                            

                            
                            #if not duplicate packet get the data
                            if sequence == expected_seq:
                                ack = Packet(sender_IP=self.sender_IP, 
                                                sender_port=self.sender_port, 
                                                dest_IP=socket.inet_ntoa(sender), 
                                                dest_port=sender_port ,sequence=expected_seq, 
                                                data=None, 
                                                ack=expected_seq,
                                                syn=False,is_ack=True).build()
                                
                                self.lock.acquire()
                                
                                if ((floor(self.max_window_size/1024) - len(self.buffer) >= 1) or (self.max_window_size == 0)):
                                    #read the data from the buffer
                                    data_chunk = header[32:]
                                    #push byte by byte into buffer
                                    self.buffer.append(data_chunk)

                                    self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                                    expected_seq += 1
                                else:
                                    print("buffer full, throwing away packet")
                                self.lock.release()
                                
                            elif sequence > expected_seq:#if there is loss,then send duplicate ack
                                self.lock.acquire()
                                print("LOSS detected!!!!!!!!!!")
                                print("\t expecting packet {} but got packet {}".format(expected_seq, sequence))
                                ack = Packet(sender_IP=self.sender_IP, 
                                                sender_port=self.sender_port, 
                                                dest_IP=socket.inet_ntoa(sender), 
                                                dest_port=sender_port ,sequence=expected_seq-1, 
                                                data=None, 
                                                ack=expected_seq - 1,
                                                syn=False,is_ack=True).build()
                                
                                self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                                self.closed = True
                                self.listening = False
                                self.lock.release()
                            
                    except TimeoutError as e:
                        print("server has not received anything for 75 seconds, closing connection")
                        self.closed = True
                        self.listening = False
                        return
                print("stopped listening")
            else:
                print("cannot listen for packets, connection is closed")
        else:
            print("cannot listen for packets while sending.")

    
    def receive_data(self,data):
        data = floor(data/1024)
        timer = Timer(self.recv_timeout)
        while len(self.buffer) == 0:
            timer.start()
            time.sleep(0.01)
            if timer.notify_timeout():
                raise TimeoutError('connection has timed out')
            

        if data >= len(self.buffer):
            self.lock.acquire()
            x = b''
            for i in range(len(self.buffer)):
                chunk = self.buffer.pop(0)
                x+=chunk
            self.lock.release()
            return x
        
        else:
            self.lock.acquire()
            x = b''.join(self.buffer[:data])
            self.buffer = self.buffer[data:]
            self.lock.release()
            return x
        
    def is_listening(self):
        return self.listening
    
    def set_timeout(self, time):
        self.recv_timeout = time
    
    def close(self):
        self.lock.acquire()
        close_pack = Packet(self.sender_IP,self.sender_port, self.dest_IP,self.dest_port ,sequence=0, data=None,ack=0,fin=True).build()
        self.socket.sendto(close_pack,(self.dest_IP,self.dest_port))
        
        self.socket.settimeout(0.3)
        data, addr = self.socket.recvfrom(1000)
        ack = struct.unpack('!4s4sIHHIIHHHxx',data)
        flags = ack[7]
        checksum = ack[9]
        seq = ack[5]
        print("THE FIN ACK HAS SEQUENCE NUMBER {}".format(seq))
        if (Packet.validate_packet(packet=data,checksum=checksum) == False):#check valid
            print("closure failed: bad checksum! ")
        elif (not(flags & (1 << 7))):#check ack
            print("closure failed:or the packet received is not an ack! ")
        elif not(flags & (1 << 5)):#check fin
            print("closure failed:  ack received is not a fin ack")
        
        self.closed = True
        print("connection closed")
        self.lock.release()