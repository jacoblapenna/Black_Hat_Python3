

import sys
import socket


target_host = "127.0.0.1"
target_port = 9999

#create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#AF_INET sets up a standard IPv4 address or hostname
#SOCK_STREAM indicates this will be a TCP client

#connect the client
client.connect((target_host, target_port))

#send some data
message = "GET / HTTP/1.1\r\nHost: google.com\r\n\r\n"
client.send(message.encode())

#receive some data
response = client.recv(4096)

sys.stdout.write(response.decode("utf-8") + '\r\n')


# https://docs.python.org/3.6/howto/sockets.html#socket-howto
