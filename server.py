from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
from unittest import case

from blackjack import Blackjack
#from traceback import print_tb
#from xml.dom.domreg import registered

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
    
    Client to server tokens
    1: General chat
    2: return requested input. this requires specification od type of desired input.
        2 0: request string
        2 1: request int
        2 2: request number type
    3: signup process
    4: heart beat check (unsure persistent connection)
"""

BUFFER_SIZE_CST = 8192


class Server:
    server_ports = set()

    User_connected = set()
    User_connected_lock = threading.Lock()

    def __init__(self, game_type = "BlackJack" ,player_allowed=100, BUFFER_SIZE = BUFFER_SIZE_CST, port=12000, host='127.0.0.1', TIMEOUT = 2, rule_function = None):
        self.game_type = game_type
        self.game_rules = rule_function
        #self.game = Blackjack()
        self.game_state = "Waiting"
        self.check_port_availibility(port)
        self.port = port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.host = host
        self.player_allowed = player_allowed
        self.TIMEOUT = TIMEOUT

        #all the next block serve the same function of handling received messages via different threads(#00000000 mark end of block)
        #tasks received
        self.receive_queue = queue.Queue()
        self.receive_queue_lock = threading.Lock()


        #message marked 2
        self.response_back = None   # (uuid, response)
        self.response_back_event = threading.Event()

        #Message marked with a 3
        self.registering_received = None
        self.registering_lock = threading.Lock()
        self.registering_lock.acquire()
        #000000000000000000000

        self.database = Database() # handles users data long term

        #players
        self.clients = dict()   #has volatile data. stores sockets {uuid: (client_socket, user_name, thread)}. thread is the thread responsible for receiving this user's input
        self.in_game_lock= threading.Lock()
        self.in_game = set()   #players in the game
        self.in_lobby_lock = threading.Lock()
        self.in_lobby = set()   #player waiting for game to end

        self.ignore = dict() # uuid : nbr . nbr stand for how many times to ignore the user. if user take time to answer and program skips. we should ignore the delayed answer
        #self.disconnected = set() #player that are disconnected in game

        self.start_server()


    def check_port_availibility(self, port): #thinking about having multiple servers for maybe multiple games
        if port not in Server.server_ports:
            Server.server_ports.add(port)
        else:
            print('Port already used')
            del self

    def send_all(self, message, response_back = False, timeout = None):
        for player in self.clients.keys():
            self.send_to_uuid(player, [2 if response_back else 1, message])

    def send_all_in_game(self, message, response_back = False, timeoutt = 0):
        start_time = time.time()
        response = dict()
        for player in self.in_game:
            if type(message) == list:
                self.send_to_uuid(player, [2 if response_back else 1]+message)
            else:
                self.send_to_uuid(player, [2 if response_back else 1, message])

        if response_back:
            try:
                while len(response.keys()) < len(self.in_game):  # and not timeout or start_time + timeout < time.time():
                    self.response_back_event.wait(timout = start_time + timeoutt - time.time())
                    response[self.response_back[0]] = self.response_back[1]
                    self.response_back_event.clear()
            except:
                for player in self.in_game:
                    if player not in response.keys():
                        self.ignore[player] += 1
            return response





    def send_all_in_lobby(self, message, response_back = False):
        for player in self.in_game:
            self.send_to_uuid(player, [2 if response_back else 1, message])


    def send_to_uuid(self, uuid, message):
        self.send_client(self.clients[uuid][0],message)

    def send_client(self, connection_socket, message):
        if type(message) != list or type(message)!= tuple:
            message = [message]
        if message[-1] != END_TOKEN:
            message.append(END_TOKEN)
        for item in message:
            connection_socket.sendall(struct.pack(item) if utils.is_type_number(item) else item.encode())



    def receiving(self, client_socket): #get data from client x
        text = ""
        end_token = False
        while not end_token:
            text += client_socket.recv(self.BUFFER_SIZE)
            if text[-len(END_TOKEN.encode()):] == END_TOKEN.encode():  # look if the received ends with END_TOKEN token
                end_token = True
        self.receive_queue.put(text[:-len(END_TOKEN.encode())])

    #before threading
    """def get_player_connections(self, server_socket):
        start_time = time.time()
        while start_time + 60 > time.time():
            connection_socket, client_addr = server_socket.accept()
            self.get_uuid()
            self.clients[] = connection_socket
            print(f'New client with address {client_addr}')"""
    def ask_user_name(self, client_socket):
        self.send_client(client_socket, [2,'What is your session username?'])
        self.registering_lock.acquire()
        return self.registering_received

    def get_uuid(self, client_socket):
        pass


    def get_player_connections(self, server_socket): #thread that runs forever to get new connections
        while True:
            client_socket, client_addr = server_socket.accept()
            #self.get_uuid(connection_socket)
            #self.send_client(client_socket, [3])
            thread = threading.Thread(target=self.receiving, args=(client_socket,))
            thread.setDaemon(True)
            thread.start()
            self.registering_lock.acquire()
            registered = bool(self.registering_received)  #if empty string false. else it's the user's uuid
            """if not registered: #create account
                    self.send_client(client_socket, [3,'You have no account registered. Do you want to register one? type "yes" for confirmation'])
                    with self.registering_lock:
                        self.registering_lock.acquire()
                        if self.registering_received.lower() != "yes": 
                            client_socket.close()
                            return"""
            uuid = self.database.get_uuid_data(self.registering_received if registered else None)
            user_name = self.ask_user_name(client_socket)

            if not registered:
                self.send_client(client_socket, [3,uuid])
            if self.game_rules: self.send_client(client_socket,[1,self.game_rules()])

            self.in_game_lock.acquire()
            self.in_lobby_lock.acquire()

            if self.game_state == "Waiting":
                self.in_game.add(uuid)
            else:
                self.in_lobby.add(uuid)

            self.in_game_lock.release()
            self.in_lobby_lock.release()


            self.clients[uuid] = client_socket, user_name, thread

            print(f"Server: {"new" if not registered else ""} User {self.registering_received} logged in as {user_name}")


    def treating_queue(self):
        while True:
            request = self.receive_queue.get(block=True)
            match struct.unpack('!I',request[:4])[0]:
                case 1:
                    continue
                case 2:
                    while self.response_back_event.is_set():
                        continue #wait until response back is consumed by request_user_input()
                    self.response_back = (request[4:36+4], request[36+4:])   # 4 token, 36 is len of uuid
                    if self.ignore[self.response_back[0]] == 0:
                        self.response_back_event.set()
                    elif self.ignore[self.response_back[0]]> 0:
                        self.ignore[self.response_back[0]] -= 1
                    else:
                        print(f"self.ignore of uuid({self.response_back[0]}) equal to {self.ignore[self.response_back[0]]}. not supposed to be negative")

                case 3:
                    self.registering_received = request[4:].decode()
                    self.registering_lock.release()
                case 4:
                    continue
                case _:
                    print(f"Unrecognized request {struct.unpack('!I',request[:4])[0]} received")



    def request_user_input(self, uuid, message, timout = None):
        self.send_to_uuid(uuid, message)
        received = None
        try:
            self.response_back_event.wait(timout)
            received = self.response_back.copy()
            self.response_back_event.clear()
        except:
            self.ignore[uuid] += 1
        return received


    def start_server(self):
        with (socket(AF_INET, SOCK_STREAM) as server_socket):

            server_socket.bind((self.host, self.port))
            server_socket.listen(self.player_allowed)
            server_socket.settimeout(self.TIMEOUT)
            print('Server is ready')  # done with step 1

            #self.get_player_connections(server_socket)
            connections = threading.Thread(target=self.get_player_connections) #gets new connections
            #self.receiving(server_socket)
            #receiving = threading.Thread(target=self.receiving) #Get TCP messages sent by clients
            treat_received_messages = threading.Thread(target=self.treating_queue)
            connections.start()
            treat_received_messages.start()



#to test
#Connections more that self.player_allowed
#User takes forever to input username. causing blockage in new connections

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


"""""

with socket(AF_INET, SOCK_DGRAM) as server_socket:
    server_socket.settimeout(TIMEOUT)

    server_socket.bind((HOST, PORT))
    print('Server is ready')

    while True:

        # STEP 2: receive a message and the client's address
        try:
            message, client_addr = server_socket.recvfrom(BUFFER_SIZE)

            print(f'Message from client with address {client_addr}')

            # STEP 3: convert incoming message to uppercase

            text = message[4:].decode() # converts bytes to string
            print(f"Server debug full text received: {text}")
            print(f"Server debug received text without struct: {text}")
            print(f"Server debug received struct: {struct.unpack('!I',message[:4])}")

            match struct.unpack('!I',message[:4])[0]:
                case 1:
                    message = text.upper()
                case 2:
                    message = text.lower()
                case 3:
                    message = text
                case 4:
                    message = text[::-1]
                case 99:
                    message = "Please insert valid command at the start of the message"
                case 0:
                    message = "See you soon. Goodbye!"
                case _:
                    print('Server error: unknown command') #just in case

            server_socket.sendto(message.encode(), client_addr)
        except TimeoutError:
            print(f'Server timed out. No data received from client for {TIMEOUT} seconds')

"""