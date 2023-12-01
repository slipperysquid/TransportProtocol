import socket
from Packet import Packet
import struct
import time



class Connection():


    def __init__(self,sender_IP,sender_port,dest_IP,dest_port,socket):
        self.sender_IP = sender_IP
        self.sender_port = sender_port
        self.socket = socket
        self.dest_IP = dest_IP
        self.dest_port = dest_port
        self.windowsize = 1
    

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
        N = 5
        next_seq_num = 0
        timer_started = False
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
                elif (ack_num == window_base):
                    window_base += 1
                    print("inscreased window base to {}".format(window_base))
            except socket.timeout:
                print("packet time out")
                start_time = time.time()
                timer_started = True
                print(window_base)
                print(ack_num)
                for i in range(window_base,next_seq_num - 1):
                    packet = Packet(self.sender_IP, self.sender_port, self.dest_IP,  self.dest_port, sequence=next_seq_num, data = chunks[next_seq_num],ack=0 ).build()
                    self.socket.sendto(packet,(self.dest_IP,self.dest_port))
                    print("sending packet with sequence number {}".format(i))
            
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


    def receive_data(self):

        prev_seq = 0
        recieve = True
        output = []
        while recieve:
            header,addr = self.socket.recvfrom(1056)
            sender,dest,length,sender_port,dest_port,sequence,ack,flags,recw,checksum = struct.unpack("!4s4sIHHIIHHHxx", header[:32])
            print("received sequence number = ", sequence)
            print("received ack number = ",ack)
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
            elif Packet.validate_packet(packet=header, checksum=checksum) and sequence == prev_seq:
                print("validated packet we seq ", sequence)
                ack = Packet(sender_IP=self.sender_IP, 
                                    sender_port=self.sender_port, 
                                    dest_IP=socket.inet_ntoa(sender), 
                                    dest_port=sender_port ,sequence=prev_seq, 
                                    data=None, 
                                    ack=prev_seq,
                                    syn=False,is_ack=True).build()
                prev_seq += 1
                self.socket.sendto(ack, (self.dest_IP,self.dest_port))
                #read the data from the buffer
                data_chunk = header[32:]
                output.append(data_chunk)
                
            else:
                #send previous ack
                ack = Packet(sender_IP=self.sender_IP, 
                                    sender_port=self.sender_port, 
                                    dest_IP=socket.inet_ntoa(sender), 
                                    dest_port=sender_port ,sequence=prev_seq-1, 
                                    data=None, 
                                    ack=prev_seq,
                                    syn=False,is_ack=True).build()
                
                self.socket.sendto(ack, (self.dest_IP,self.dest_port))

        #print("we received this: {}".format(output))
        return b''.join(output)

