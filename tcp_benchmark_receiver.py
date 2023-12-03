import socket
import time


sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

sock.bind(("0.0.0.0",5001))

sock.listen()

sock.accept()