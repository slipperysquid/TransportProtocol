from Timer import Timer
import threading
import time
import socket
import struct
from Packet import Packet
import select
import random
from math import floor
class sender():
    #shared resources

    def __init__(self,socket:socket.socket,sender_IP,sender_port,dest_IP,dest_port):
        self.timeout = 0.3
        self.dest_IP = dest_IP
        self.dest_port = dest_port
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        #shared variables for threads
        self.lock = threading.Lock()
        self.timer = Timer(self.timeout)
        self.window_base = 0
        self.N = 1
        self.socket = socket
        self.done = False
        self.next_seq_num = 0
        self.event  = threading.Event()


    def send_data(self,data,max_win_size):
        #split data into chunks
        chunks = []
        while len(data) >= 1024:
            chunks.append(data[0:1024]) 
            data = data[1024:]
        if len(data) > 0:
            chunks.append(data)
        #begin GBN
        #shared variables between data sender and ack receiver thread
        self.lock.acquire()
        self.timer = Timer(self.timeout)
        self.window_base = 0
        self.N = 1
        self.lock.release()
        self.event.clear()
        #end of shared variables
        self.next_seq_num = 0
        #starting ack receiver thread
        receiver_thread = threading.Thread(target=self.receive_ack)
        receiver_thread.start()
        print("LENGTH OF THE PACKETS IS {}".format(len(chunks)))
        while not(self.done):
    
            self.lock.acquire()
            #check if window is > max window size
            if (self.N > floor(max_win_size/1024)):
                self.N = floor(max_win_size/1024)
            #checks if window goes past chunks
            if ( self.window_base + self.N >= len(chunks)):
                self.N = len(chunks)-1
            #if the sequence number is within the window, send packets
            while ((self.next_seq_num <= self.window_base + self.N) and (self.next_seq_num <= len(chunks) - 1)):
                print("sending packet with sequence number {}".format(self.next_seq_num))
                
                
                packet = Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=self.next_seq_num, data = chunks[self.next_seq_num],ack=0 ).build()
                self.socket.sendto(packet,(self.dest_IP,self.dest_port))  
                #start timer after sending packing if the sequence number is the window base
                if (self.window_base == self.next_seq_num):
                    self.timer.start()

                self.next_seq_num += 1
            #wait a bit for the receiver thread to run
            if (not self.timer.notify_timeout()) and (self.timer.is_timing()):
                self.lock.release()
                
                time.sleep(self.timeout/10)
                self.lock.acquire()
            
            #handle timeout loss if timeout
            if self.timer.notify_timeout():
                print("LOSS DETECTED: ack time out, resetting window size to 1 ")
                
                '''for i in range(window_base,next_seq_num - 1):
                    packet = Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                    self.socket.sendto(packet,(self.dest_IP,self.dest_port))
                    print("sending packet with sequence number {}".format(i))
                '''
                self.timer.stop()
                self.N = 1
                self.next_seq_num = self.window_base

            if(self.window_base >= len(chunks) - 1):
                    print("breaking")
                    self.done = True
                    self.event.set()
                    break
                    
            self.lock.release()
            
        self.lock.release()
        receiver_thread.join()
        print("Done sending, informing server")
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
        

        print("done sending confirmed")


    def receive_ack(self):
        while not(self.done):
            if self.event.is_set():
                break
            self.lock.acquire()
            if select.select([self.socket], [], [], 0.0001)[0]:
                
                ack_data,addr = self.socket.recvfrom(32)
                ack = struct.unpack('!4s4sIHHIIHHHxx',ack_data)
                flags = ack[7]
                ack_num = ack[6]
                checksum = ack[9]
                print("ack {}  received".format(ack_num))
                #validate the ack
                if (Packet.validate_packet(packet=ack_data,checksum=checksum) == False):#check valid
                    print("Ack received is not valid")
                elif (not(flags & (1 << 7))):#check ack
                    print("Packet received is not an ack")
                    
                elif (ack_num < self.window_base):
                    print("\t LOSS DETECTED: duplicate ack received, resetting window size to 1")
                    
                    self.timer.stop()
                    self.next_seq_num = ack_num + 1
                    self.window_base = ack_num + 1
                    self.N = 1
                    self.lock.release()  
                elif (ack_num >= self.window_base):
            
                    self.timer.stop()
                    self.next_seq_num = ack_num + 1
                    self.window_base = ack_num + 1
                    self.N += 1
                    print("\tGood ack")
                    print("\tinscreased window base to {}".format(self.window_base))
                    print("\tCongestion Control: increased window size by one. Curr window size: {}".format(self.N))
                    self.lock.release()  
            else:
                time.sleep(0.0001)
                self.lock.release()   
            
            
            
            
            