#!/usr/bin/env python3

import socket
from multiprocessing import Process

"""
Socket API:

socket() # create socket object
bind() # bind it to a specified location (e.g. host and port)
listen() # listen
accept() # accept connections and create new socket on connection
connect() # connect to a bound socket
connect_ex() #
send() # send bytes
recv() # receive bytes
close() # close and cleanup socket object

"""

"""

SERVER:
socket
  |
  |
bind
  |
  |
listen
  |                  CLIENT:
  |                  socket
accept                 |
  |                    |
  |<---------------->connect # 3 way handshake
  |                    |
  |                    |
recv<----------------send # send bytes to server
  |                    |
  |                    |
send---------------->recv # get response
  |                    |
  |                    |
recv<----------------send # send more...
  .                    .
  .                    .
  .                    .
  .                  close # disconnect
close # disconnect

"""

def echo_server():

    HOST = '127.0.0.1' # "loopback" interface (i.e. localhost)
    PORT = 65432 # non-privelaged port > 1023

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT)) # bind s to the specified address
        s.listen() # listen for connections to address
        # code holds for connection
        conn, addr = s.accept() # once connection detected, create new socket conn
        with conn:
            print('Server:', f'Incoming connection from: {addr[0]}:{addr[1]}') # the clients address
            while True: # receive and echo back forever
                data = conn.recv(1024) # receive
                if not data: # or, at least, until there's no data
                    break
                print('Server:', f'Received "{data.decode()}" from the client.')
                conn.sendall(data) # echo

def echo_client():

    TARGET_HOST = '127.0.0.1'
    TARGET_PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TARGET_HOST, TARGET_PORT))
        send_str = 'Hello, World!'
        s.sendall(send_str.encode())
        data = s.recv(1024)

    print('Client:', f'Received "{data.decode()}" from the server.')

if __name__ == "__main__":

    server_process = Process(target=echo_server)
    server_process.start()

    client_process = Process(target=echo_client)
    client_process.start()
