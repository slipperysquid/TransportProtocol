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
        while not(self.done):
    
            self.lock.acquire()
            #check if window is > max window size
            if (max_win_size != 0 and self.N > (floor(max_win_size/1024) - 1)):
                self.N = floor(max_win_size/1024) - 1
            #checks if window goes past chunks
            if ( self.window_base + self.N >= len(chunks)):
                self.N = len(chunks)-1
            #if the sequence number is within the window, send packets
            while ((self.next_seq_num < self.window_base + self.N) and (self.next_seq_num <= len(chunks) - 1)):
                
                
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
                self.timer.stop()
                self.N = 1
                self.next_seq_num = self.window_base

            if(self.window_base >= len(chunks) - 1):
                    self.done = True
                    self.event.set()
                    break
                    
            self.lock.release()
            
        self.lock.release()
        receiver_thread.join()


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
                    self.lock.release()  
            else:
                time.sleep(0.0001)
                self.lock.release()   
            
            
            
            
            