###  # -*- coding: UTF-8 -*-

import sys
import socket
# import thread
import threading

try:
    '''
        #* Passar uma string VAZIA significa que o servidor também pode ouvir conexões de entrada de outros computadores.
        #> Se fosse passado 127.0.0.1, então ele ouviria apenas as chamadas feitas dentro do PC local.
    '''
    HOST = ''  # localhost
    # reserve uma PORT neste PC
    PORT = 1025

    s = socket.socket() # cria objeto socket
    print('Socket criado com sucesso')

    s.bind((HOST, PORT))

    print('socket escutando em %s' %(PORT))

    s.listen(5) # põe socket em modo escuta
    print ('socket está escutando')

    i = 0

    def main(c,numOfThread):
        while True:
            rcvdData = c.recv(1024).decode()
            print(f'Thread: {numOfThread+1} S: {rcvdData}')

            sendData = input('N: ')
            c.send(sendData.encode())

            if(sendData.lower() == 'bye'):
                break

        c.close()

    while True:
        c, addr = s.accept()
        print('Conexão estabelecida com', addr)

        # thread.start_new_thread(main,(c,i,))
        t1 = threading.Thread(target=main, args=(c,1,))
        t1.start()
        t1.join()

        i+=1

        s.close()

except KeyboardInterrupt:
    print(f'Fechando a conexão e liberando a porta {PORT}.')
    c.close()
    sys.exit()



    # # a forever loop until we interrupt it or
    # # an error occurs
    # while True:

    #     # Establish connection with client.
    #     c, addr = s.accept()
    #     print ('Conexão estabelecida com', addr)

    #     # send a thank you message to the client. encoding to send byte type.
    #     c.send('Gratiluz por conectar'.encode())

    #     # Close the connection with the client
    #     c.close()
    #     print('socket fechado')

    #     # Breaking once connection closed
    #     break

