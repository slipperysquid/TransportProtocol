# TransportProtocol
transport protocol using UDP.

Uses Go-Back-N sending technique

Implements flow control and congestion control.

Can be faster than tcp!!!!

#Usage
Protocol.conn(dest_IP,dest_port,max_window_size=0)

      Sends connection request to target and does 3 way handshake
      dest_IP:String -> destination IP
      dest_port:int -> destination port
      max_window_size:int -> receive buffer size in bytes, default: infinite
      Returns -> Connection() object

Protocol.accept(max_window_size=0)

      Accepts incomming connection requests and does 3 way handshake
      max_window_size: receive buffer size in bytes, default: infinite
      Returns -> Connection() object    
      
Connection.send_data(data)

      Sends data to other side of connection
      data:bytes -> data to send in bytes
      
Connection.receive_data(data):

      Reads bytes from the receive buffer. Blocks until there is enough data in the buffer, throws TimeoutError when timing out.
      data:int -> number of bytes to read from the buffer

Connection.set_timeout(time):

      Sets amount of time before Connection.receive_data() times out.
      time:float-> timeout time

Connection.is_listening()

      returns True if this side of the connection is listening for packets

Connection.close()

      Closes connection

# Implementation
The socket we used is a UDP socket. To ensure our socket is connection-oriented, we implemented a 3-way handshake between the sender and receiver. The sender sends an initial packet to the receiver to initiate a connection. Upon receiving this packet, the receiver sends an acknowledgement (ack) to establish the connection. Once the ack is successfully received by the sender, the connection is established, and it sends one last packet back to the receiver. After a connection is made, the receiver will listen for packets until a fin bit is given or it does not receive a packet for 75 seconds. The connection is then closed.

We decided to use the Go-Back-N (GBN) protocol with Reliable Data Transfer (RDT). The sender takes in the data and divides it into chunks of 1024 bytes. Each chunk is packaged into a packet with a sequence number and is sent across the protocol. After sending a packet, we initiate a timer to wait for an ack for the packet where the sequence number is equal to the window base. Upon successfully receiving and validating the ack, we increase the window size and move the window base to sequence + 1. The receiver receives the packets, validates them and checks to make sure the sequence number lines up with the expected sequence number. If it does, the receiver returns an ack for the latest packet, otherwise it returns for the previous packet. If the sender receives an ack out of order, the previous packets were successfully received. This ensures pipelined and safe data transfer.
 
We implemented congestion control through sawtooth window AIMD. On the sender side, we implemented a sliding window that begins at size N=1. Every time we receive an ack, we increase the window size by 1. We detect loss through duplicate acks or timeouts. If the program detects loss, we reset the window size to 1, and resend the lost packet. 

For flow control, on the receiver side, we implement a buffer. The size of the buffer can be defined by the user by passing through the number of bytes for the buffer. If no buffer size is defined, the buffer size is infinite. During the 3 way handshake at the start of the connection, receive window sizes are traded. When a sender is sending, the number of inflight packets cannot exceed the max size of the buffer divided by the size of a packet.


      
