import socket

HOST = '127.0.0.1'  # localhost
PORT = 1025


# Cria um socket TCP/IP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Liga o socket ao endereco e porta especificados
s.bind((HOST, PORT))
print 'Servidor escutando em', HOST, 'na porta', PORT

# Coloca o socket em modo de escuta
s.listen(2)

while True:
    print('Aguardando conexao...')

    # Aguarda por novas conexoes
    conn, add = s.accept()
    print('Conexao estabelecida de:', add)

    # Recebe os dados do cliente
    data = conn.recv(1024)

    if not data:
        print("Nenhum dado recebido")
    else:
        print('Mensagem recebida:', data.decode())

# Fecha o socket da conexao atual
conn.close()
print 'conexao finalizada'

s.listen(10)  # Verificar se o nmero de conexes possveis pode afetar o funcionamento do nosso software
conn, add = s.accept()
print "Conectado a " + add[0] + ":" + str(add[1])

data = None
while True:
    data = conn.recv(1025)  # Tamanho do Buffer settado para o mesmo que o da comunicao com o DSSim
    # print data
    # print type(data)
    # if not data:
        #  break
    if data is not None:
        print 'Mensagem recebida:' + data.decode()
        # decodifica_mensagem(data)
        # resposta = process_data(data)
    # if resposta is not None:
    #     conn.sendall(resposta)

conn.close()  # Verificar como arrumar essa questo do trmino da comunicao.
s.close()
print 'conexao finalizada'
