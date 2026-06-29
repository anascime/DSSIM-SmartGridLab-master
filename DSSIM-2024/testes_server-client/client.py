###  # -*- coding: UTF-8 -*-
import sys
import socket

try:
    # Create a socket object
    s = socket.socket()

    # Define the port on which you want to connect
    PORT = 1024
    HOST = '127.0.0.1'

    # connect to the server on local computer
    s.connect((HOST, PORT))

    while True:
        # str = input('')
        str = b'\x01\x15\x00\x12\x00\x00\x05\x08I\x00\x00\x05\x07I\x00\x00\x05(H\x00\x00'
        s.send(str)  # send message

        if str.lower() == 'bye':
            break

        # receive data from the server and decoding to get the string.
        # print (s.recv(1024).decode())
    # close the connection
    s.close()

except KeyboardInterrupt:
    print(f'Fechando a conexão e liberando a porta {PORT}.')
    s.close()
    sys.exit()