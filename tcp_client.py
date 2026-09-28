from socket import socket, AF_INET, SOCK_STREAM
# AF_INET is for IPv4
# SOCK_STREAM is for TCP

SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 12000
BUFFER_SIZE = 1024

async def quiting():
    while input().lower() != 'quit':
        print(end="")
    exit(0)

with socket(AF_INET, SOCK_STREAM) as client_socket:

    client_socket.connect((SERVER_ADDR, SERVER_PORT))

    while True:
        text = input('Input sentence: ')

        client_socket.sendall(text.encode())

        modified_text = client_socket.recv(BUFFER_SIZE).decode()

        print('From Server:', modified_text)

        if text[:4].lower() == 'quit':
            break



