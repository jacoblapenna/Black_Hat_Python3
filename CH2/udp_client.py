

import sys
import socket


target_host = "127.0.0.1"
target_port = 80

#create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#AF_INET sets up a standard IPv4 address or hostname
#SOCK_DGRAM indicates this will be a UDP client

#NOTE: UDP is a "connectionless" protocol, therefore no call to client.connect()

#send some data
client.bind((target_host, target_port))
message = "AAABBBCCC"
client.sendto(message.encode(), (target_host, target_port))

#receive some data
data, addr = client.recvfrom(4096)

#print results to user
sys.stdout.write(data.decode("utf-8") + '\r\n')
sys.stdout.write('Host: ' + addr[0] + '\r\n')
sys.stdout.write('Port: ' + str(addr[1]) + '\r\n')
