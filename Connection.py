import socket
from Packet import Packet
import struct
import threading
import time
from GBN_send import sender
import random
class Connection():
    
    def __init__(self,sender_IP,sender_port,dest_IP,dest_port,socket, max_window_size):
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        self.socket = socket
        self.dest_IP = dest_IP
        self.dest_port = dest_port
        self.windowsize = 1
        self.max_window_size = max_window_size
        self.GBN_sender = sender(self.socket, self.sender_IP,self.sender_port,self.dest_IP,self.dest_port)
    

    def send_data(self,data):
        self.GBN_sender.send_data(data, self.max_window_size)

        '''
        #split data into chunks
        chunks = []
        while len(data) >= 1024:
           chunks.append(data[0:1024]) 
           data = data[1024:]
        if len(data) > 0:
            chunks.append(data)
        #begin GBN
        #shared variables between data sender and ack receiver thread
        lock = threading.Lock()
        timer = Timer()
        window_base = 0
        #end of shared variables
        N = 5
        next_seq_num = 0
        #starting ack receiver thread
        while True:
            #start the ack listening thread
            globals()['close_ack_thread'] = False
            #ack_data = self.listen_for_ack()
            if(window_base > len(chunks) - 1):
                    print("breaking")
                    break
            #if the sequence number is within the window, send packets
            while ((next_seq_num < window_base + N) and (next_seq_num <= len(chunks) - 1)):
                print("sending packet with sequence number {}".format(next_seq_num))
                packet = Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                self.socket.sendto(packet,(self.dest_IP,self.dest_port))  
                #start timer after sending packing if the sequence number is the window base
                if (window_base == next_seq_num):
                    start_time = time.time()
                    timer_started = True
                next_seq_num += 1
            #received ack with a timeout incase of loss
            try:
                self.socket.settimeout(0.3)
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
                elif (ack_num < window_base):
                    print("\t LOSS DETECTED: duplicate ack received, resetting window size to 1")
                    N = 1
                elif (ack_num == window_base):
                    window_base += 1
                    N += 1
                    print("\tGood ack")
                    print("\tinscreased window base to {}".format(window_base))
                    print("\tCongestion Control: increased window size by one. Curr window size: {}".format(N))
            #handle timeout loss
            except socket.timeout:
                print("LOSS DETECTED: ack time out, resetting window size to 1 ")
                
                ''''''for i in range(window_base,next_seq_num - 1):
                    packet = Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                    self.socket.sendto(packet,(self.dest_IP,self.dest_port))
                    print("sending packet with sequence number {}".format(i))
                ''''''
                N = 1
                next_seq_num = window_base
            
            globals()['close_ack_thread'] = True
            

        globals()['close_ack_thread'] = True
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
        '''


    def receive_data(self):

        expected_seq = 0
        recieve = True
        output = []
        while recieve:
           
            try:
                header,addr = self.socket.recvfrom(1056)
                sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx", header[:32])
                
                if (flags & (1 << 5)):
                    print('fin received')
                    ack = Packet(sender_IP=self.sender_IP, 
                                            sender_port=self.sender_port, 
                                            dest_IP=socket.inet_ntoa(sender), 
                                            dest_port=sender_port ,sequence=1, 
                                            data=None, 
                                            ack=sequence+1,
                                            fin=True, is_ack=True).build()
                    self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                    recieve = False
                    

                #check corruption
                elif Packet.validate_packet(packet=header, checksum=checksum):
                    print("validated packet with sequence number ", sequence)
                    
                    x = random.randint(0,9)

                    
                    #if not duplicate packet get the data
                    if sequence == expected_seq:
                        ack = Packet(sender_IP=self.sender_IP, 
                                        sender_port=self.sender_port, 
                                        dest_IP=socket.inet_ntoa(sender), 
                                        dest_port=sender_port ,sequence=expected_seq, 
                                        data=None, 
                                        ack=expected_seq,
                                        syn=False,is_ack=True).build()
                        if x < 8:
                            self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                        expected_seq += 1
                        #read the data from the buffer
                        data_chunk = header[32:]
                        output.append(data_chunk)
                    elif sequence > expected_seq:#if there is loss,then send duplicate ack
                        print("LOSS detected!!!!!!!!!!")
                        print("\t expecting packet {} but got packet {}".format(expected_seq, sequence))
                        ack = Packet(sender_IP=self.sender_IP, 
                                        sender_port=self.sender_port, 
                                        dest_IP=socket.inet_ntoa(sender), 
                                        dest_port=sender_port ,sequence=expected_seq-1, 
                                        data=None, 
                                        ack=expected_seq - 1,
                                        syn=False,is_ack=True).build()
                        if x < 8:
                            self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                    
            except Exception as e:
                print(e)
                '''
            else:
                #send previous ack
                ack = Packet(sender_IP=self.sender_IP, 
                                    sender_port=self.sender_port, 
                                    dest_IP=socket.inet_ntoa(sender), 
                                    dest_port=sender_port ,sequence=expected_seq-1, 
                                    data=None, 
                                    ack=expected_seq - 1,
                                    syn=False,is_ack=True).build()
                
                self.socket.sendto(ack, (self.dest_IP,self.dest_port))
'''
        #print("we received this: {}".format(output))
        return b''.join(output)

