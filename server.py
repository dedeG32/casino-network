import uuid
import json
from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
from database import Database
import struct
import utils
import queue

END_TOKEN = "<[{.o___o.}]>"


#SERVER_STATES = ("READY", "RUNNING")

"""
    Server to client message tokens (User != client. client is the local machine script (automatic). User is the person behind the client (human))
    1: print
    2: print and need User input
    3: need client response. send UUID else blank
    4: need client response. send heart beat check (unsure persistent connection)

"""

class Server:
    server_ports = set()
    User_connected = set()
    def __init__(self, game = "BlackJack" ,player_allowed=100, BUFFER_SIZE=1024, port=12000, host='127.0.0.1', TIMEOUT = 2):
        self.game = game
        self.check_port_availibility(port)
        self.port = port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.host = host
        self.player_allowed = player_allowed
        self.TIMEOUT = TIMEOUT

        self.receive_queue = queue.Queue()

        self.database = Database() # handles users data long term
        self.users = dict() # has permanent data. Should be stored after disconnection
        self.clients = dict()   #has volatile data
        self.retreive_data()

        self.start_server()


    def check_port_availibility(self, port): #thinking about having multiple servers for maybe multiple games
        if port not in Server.server_ports:
            Server.server_ports.add(port)
        else:
            print('Port already used')
            del self

    def genrate_uuid(self):
        new_uuid =  str(uuid.uuid4())
        self.users[new_uuid] = (1500, "User") #tokens, role
        return new_uuid

    def retreive_data(self):
        with open("data.json", "r") as file:
            self.users = json.load(file)

    def send_client(self, connection_socket, message):
        if type(message) != list:
            message = [message]
        message.append(END_TOKEN)
        for item in message:
            connection_socket.sendall(struct.pack(item) if utils.is_type_number(item) else item.encode())



    def receive(self, uuid): #get data from client x
        #modified_text = client_socket.recv(BUFFER_SIZE).decode()
        pass

    #before threading
    """def get_player_connections(self, server_socket):
        start_time = time.time()
        while start_time + 60 > time.time():
            connection_socket, client_addr = server_socket.accept()
            self.get_uuid()
            self.clients[] = connection_socket
            print(f'New client with address {client_addr}')"""

    def get_uuid(self, client_socket):
        self.send_client(client_socket,[3])
        self.receive(client_socket)


    def get_player_connections(self, server_socket): #thread that runs forever to get new connections
        while True:
            connection_socket, client_addr = server_socket.accept()
            self.get_uuid(connection_socket)

            self.clients[] = connection_socket
            print(f'New client with address {client_addr}')

    def start_server(self):
        with (socket(AF_INET, SOCK_STREAM) as server_socket):

            server_socket.bind((self.host, self.port))
            server_socket.listen(self.player_allowed)
            server_socket.settimeout(self.TIMEOUT)
            print('Server is ready')  # done with step 1

            while True:
                self.get_player_connections(server_socket)


                with connection_socket:
                    run = True

                    # STEP 3: read request from client
                    while run:
                        # text = list()
                        text = ""
                        end_token = False
                        while not end_token:
                            # text.append(connection_socket.recv(BUFFER_SIZE).decode()) # decode converts bytes to string
                            text += connection_socket.recv(BUFFER_SIZE).decode()
                            print(text, " ", text[-4:] == END_TOKEN)
                            if text[-4:] == END_TOKEN:  # look if the received ends with \end token
                                end_token = True

                        print(f"Server debug (received list): {text}")
                        # text.pop(-1)
                        text = text[:-4]
                        print(f"Server debug (remove end_token list): {text}")
                        command_type = valid_command(text[0:7])

                        if command_type == 0:  # quiting
                            connection_socket.sendall("Disconnecting from server.".encode())
                            print(f"Server debug (command type == {command_type})")
                            connection_socket.sendall(END_TOKEN.encode())
                            run = False
                            continue
                        if command_type == 99:
                            connection_socket.sendall("Insert a valid command.".encode())
                            print(f"Server debug (command type == {command_type})")
                            connection_socket.sendall(END_TOKEN.encode())
                            continue

                        i = command_type  # to shorten next line
                        text = text[
                               5 if i == 1 or i == 2 else 4 if i == 3 or i == 0 else 7:]  # removes the command token from text
                        print(f"Server debug (remove command from list): {text}")

                        # for line in text:
                        # print("debug server (before modification line): ",line)
                        message = str()
                        match command_type:
                            case 1:
                                message = text.upper()
                            case 2:
                                message = text.lower()
                            case 3:
                                message = text
                            case 4:
                                message = text[::-1]
                        print("debug server (after modification line): ", message)
                        connection_socket.sendall(message.encode())
                        connection_socket.sendall(END_TOKEN.encode())

                print("Server debug: Client disconnected. Waiting for new client...")



if __name__ == '__main__':
    server = Server()

"""from socket import socket, AF_INET, SOCK_STREAM 
# AF_INET is for IPv4
# SOCK_STREAM is for TCP 

# server socket settings
HOST = '127.0.0.1' # limits to localhost; set to '0.0.0.0' for any host
PORT = 12000
BACKLOG = 3 # pending connection queue size

# connection socket settings
BUFFER_SIZE = 8192 #8192  # maximum bytes returned by single receive call
END_TOKEN = "\end"


def valid_command(command):
    if command[0:5].lower() == 'upper':
        return 1
    if command[0:5].lower() == 'lower':
        return 2
    if command[0:4].lower() == 'echo':
        return 3
    if command[0:7].lower() == 'reverse':
        return 4
    if command[0:4].lower() == 'quit':
        return 0
    else:
        return 99


# STEP 1: create a server socket for clients to make initial connection

with (socket(AF_INET, SOCK_STREAM) as server_socket):

    server_socket.bind((HOST, PORT))

    server_socket.listen(BACKLOG)

    print('Server is ready') # done with step 1

    while True:

        # STEP 2: wait for incoming connection request

        connection_socket, client_addr = server_socket.accept()

        print(f'New client with address {client_addr}')

        with connection_socket:
            run = True

        # STEP 3: read request from client
            while run:
                text = ""
                end_token = False
                while not end_token:
                    text += connection_socket.recv(BUFFER_SIZE).decode()
                    print(text, " ", text[-4:] == END_TOKEN)
                    if text[-4:] == END_TOKEN: #look if the received ends with \end token
                        end_token = True

                print(f"Server debug (received list): {text}")
                text = text[:-4]
                print(f"Server debug (remove end_token list): {text}")
                command_type = valid_command(text[0:7])

                if command_type == 0: #quiting
                    connection_socket.sendall("Disconnecting from server.".encode())
                    print(f"Server debug (command type == {command_type})")
                    connection_socket.sendall(END_TOKEN.encode())
                    run = False
                    continue
                if command_type == 99:
                    connection_socket.sendall("Insert a valid command.".encode())
                    print(f"Server debug (command type == {command_type})")
                    connection_socket.sendall(END_TOKEN.encode())
                    continue

                i = command_type #to shorten next line
                text = text[5 if i==1 or i==2 else 4 if i==3 or i==0 else 7:] #removes the command token from text
                print(f"Server debug (remove command from list): {text}")

                #for line in text:
                #print("debug server (before modification line): ",line)
                message = str()
                match command_type:
                        case 1:
                            message = text.upper()
                        case 2:
                            message = text.lower()
                        case 3:
                            message = text
                        case 4:
                            message = text[::-1]
                print("debug server (after modification line): ", message)
                connection_socket.sendall(message.encode())
                connection_socket.sendall(END_TOKEN.encode())

        print("Server debug: Client disconnected. Waiting for new client...")



"""