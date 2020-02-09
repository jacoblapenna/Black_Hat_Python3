#!/usr/bin/env python3

import types
import socket
import selectors
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

def echo_server(host, port):

    def accept_wrapper(sock):

        conn, addr = sock.accept() # create connection socket
        conn.setblocking(False) # don't hold on this socket

        # show event to user
        print('Server:', f'Incoming connection from: {addr[0]}:{addr[1]}')

        # create custom type/class for selector data
        # inb and outb are bit string attributes of the "data" class
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')

        # event is a read or wrtie event (| is the or logical operator)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        # add connection socket to selector
        sel.register(conn, events, data=data)

    def service_connection(key, mask):

        # get socket and its data
        sock = key.fileobj
        data = key.data

        if mask & selectors.EVENT_READ:

            recv_data = sock.recv(1024)

            if recv_data:
                data.outb += recv_data
            else:
                print('Server:',
                      f'Closing connection from {data.addr[0]}:{data.addr[1]}')
                # cleanup
                sel.unregister(sock) # remove socket from selector
                sock.close() # close socket

        elif mask & selectors.EVENT_WRITE:

            if data.outb:
                print('Server:',
                      f'Responding with "{data.outb.decode()}" to {data.addr[0]}:{data.addr[1]}')
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]

    # create selector
    sel = selectors.DefaultSelector()

    # create server listening socket (the main socket)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port)) # bind s to the specified address
    s.listen() # listen for connections to address
    print('Server:', f'Listening on {host}:{port}')
    # don't block application on calls to blocking methods
    s.setblocking(False)

    # add original listening socket to selector
    sel.register(s, selectors.EVENT_READ, data=None) # initially no data

    try:
        while True:

            events = sel.select(timeout=None) # list of (socket, event) tuples
            # holds until socket(s) is(are) ready for I/O

            for key, mask in events:
                if key.data is None:
                    # initiall listening socket should accept incoming connections
                    accept_wrapper(key.fileobj)
                else:
                    # already accepted connection socket to a client
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Server:", "Caught keyboard interrupt, exiting!")
    finally:
        sel.close()

def echo_client(target_host, target_port, n):

    def start_connection(host, port, num_connections):

        addr = (host, port)

        for i in range(n): # create n connections to server

            conn_id = i + 1 # set connection number

            # tell user
            print('Client:',
                  f'Attempting connection {conn_id} to server.')

            # create client side connection socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            # 'connect_ex' no exception when blocking is False
            s.connect_ex(addr)

            # sore particular event in events (either read or write event)
            events = selectors.EVENT_READ | selectors.EVENT_WRITE

            # create custom data class
            data = types.SimpleNamespace(conn_id=conn_id,
                                         msg_total=sum(len(m) for m in messages), # only possible with predefined messages
                                         recv_total=0,
                                         messages=list(messages),
                                         outb=b'')

            # add connection socket to client selector
            sel.register(s, events, data=data)

    def service_connection(key, mask):

        # get the socket and data from the args
        sock = key.fileobj
        data = key.data

        if mask & selectors.EVENT_READ:

            # get the data
            recv_data = sock.recv(1024)

            if recv_data: # if data was present
                # show user
                print('Client:',
                      f'Received: "{recv_data.decode()}"')
                # and update total bytes received
                data.recv_total += len(recv_data)

            if not recv_data or data.recv_total == data.msg_total:
                # close connection
                print('Client:',
                       f'Received entire message, closing connection {data.conn_id}')
                sel.unregister(sock)
                sock.close()

        if mask & selectors.EVENT_WRITE:

            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)

            if data.outb:
                print('Client:',
                       f'Sending "{data.outb}" to connection {data.conn_id}')
                sent = sock.send(data.outb.encode())
                data.outb = data.outb[sent:]

    # create client selector
    sel = selectors.DefaultSelector()
    # create list of messaged to send to server
    messages = ["string 1", "string 2", "string 3"]

    start_connection(target_host, target_port, n)

    try:
        while True:

            events = sel.select(timeout=1)

            if events:
                for key, mask in events:
                    service_connection(key, mask)
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print('Client:', 'Caught keyboard interrupt, exiting!')
    finally:
        sel.close()



if __name__ == "__main__":

    host = '127.0.0.1'
    port = 8080

    server_process = Process(target=echo_server, args=(host, port))
    server_process.start()

    client_process = Process(target=echo_client, args=(host, port, 2))
    client_process.start()

"""
Example behaviour below. NOTE: order is not defined. Also,
note that recv() does not have predictable streaming length.
Suggest adding application layer to sockets that allows for
headers with content descriptors so that both client and server
know what to process with recv() in advance (i.e. HTTP).

Server: Listening on 127.0.0.1:8080
Client: Attempting connection 1 to server.
Client: Attempting connection 2 to server.
Server: Incoming connection from: 127.0.0.1:49270
Server: Incoming connection from: 127.0.0.1:49272
Client: Sending "string 1" to connection 1
Client: Sending "string 1" to connection 2
Server: Responding with "string 1" to 127.0.0.1:49270
Client: Sending "string 2" to connection 1
Client: Sending "string 2" to connection 2
Server: Responding with "string 2" to 127.0.0.1:49270
Client: Received: "string 1"
Server: Responding with "string 1string 2" to 127.0.0.1:49272
Client: Sending "string 3" to connection 1
Client: Sending "string 3" to connection 2
Server: Responding with "string 3" to 127.0.0.1:49270
Client: Received: "string 2"
Client: Received: "string 1string 2"
Server: Responding with "string 3" to 127.0.0.1:49272
Client: Received: "string 3"
Client: Received entire message, closing connection 1
Server: Closing connection from 127.0.0.1:49270
Client: Received: "string 3"
Client: Received entire message, closing connection 2
Server: Closing connection from 127.0.0.1:49272
"""
