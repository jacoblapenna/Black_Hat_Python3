import sys
import socket
import threading

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except:
        print(f"[!!] Failed to listen on {local_host}:{local_port}")
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print(f"[*] Listening on {local_host}:{local_port}")

    server.listen()

    while True: # always listen for connections to accept

        client_socket, addr = server.accept()

        print(f"[==>] Received incoming connection from {addr[0]}:{addr[1]}")

        proxy_thread = threading.Thread(target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first))

        proxy_thread.start()

def proxy_handler(client_socket, remote_host, remote_port, receive_first):

    # connect to the remote host
    # consider wrapping in try with error handling
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket = socket.connect((remote_host, remote_port))

    # reveive data
    if receive_first:

        remote_buffer = receive_from(remote_socket) # handle receipt
        hex_dump(remote_buffer) # hex dump in terminal

        # handle the response
        remote_buffer = response_handler(remote_buffer)

        # if we have data send it
        if len(remote_buffer):
            print(f"[<==] Sending {len(remote_buffer)} bytes to localhost.")
            client_socket.send(remote_buffer) # may need to encode

    # start loop to: read from local, send to remote, send to local, repeat
    while True:

        # read from local
        local_buffer = receive_from(client_socket)

        if len(local_buffer):

            print(f"[==>] Received {len(local_buffer)} from localhost.")
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)

            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # receive response
        remote_buffer = receive_from(remote_socket)

        if len(remote_socket):

            print(f"[<==] Received {len(remote_buffer)} bytes from remote.")
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)

            client_socket.send(remote_buffer)

            print("[<==] Sent to localhost.")

        # if no more data on either side, close the connections
        if not len(local_buffer) or len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closed connections.")

            break

def hexdump(src, length=16):
    """ dump hex values """

    results = []

    if isinstance(src, unicode):
        digits = 4
    else:
        digits = 2

    for i in range(0, )

def receive_from(connection):
    pass # needs work

def request_handler(buffer): # packets destined for remote host

    # perform desired packet modifications here

    return buffer

def response_handler(buffer): # packets destined for remote host

    # perform desired packet modifications here

    return buffer

if __name__ == "__main__":

    # make sure command is what we're expecting
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [local_host] [local_port] [remote_host] [remote_port] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)

    # setup local listening params
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # setup remote target params
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # listen and recieve before sending?
    if sys.argv[5] == 'True':
        receive_first = True
    else: # consider adding test for non bool and non caps
        receive_first = False

    # start the listening socket
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)
