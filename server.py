from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
from unittest import case

#from blackjack import Blackjack
#from traceback import print_tb
#from xml.dom.domreg import registered

from database import Database
import struct
import utils
import queue

END_TOKEN = "<[{.o___o.}]>"

DEBUG_SERVER = True

#SERVER_STATES = ("READY", "RUNNING")

"""
    Server to client message tokens (User != client. client is the local machine script (automatic). User is the person behind the client (human))
    1: print
    2: print and need User input
        2 0: request string
        2 1: request int
        2 2: request number type
    3: need client response. send UUID else blank
    4: need client response. send heart beat check (unsure persistent connection)
    
    Client to server tokens
    1: General chat
    2: return requested input. this requires specification od type of desired input.
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
        self.server_open = True #keeps connections open

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

    def debug_send(self, what_sent):
        if DEBUG_SERVER : print(f"debug server (send): {what_sent}")


    def check_port_availibility(self, port): #thinking about having multiple servers for maybe multiple games
        if port not in Server.server_ports:
            Server.server_ports.add(port)
        else:
            print('Port already used')
            del self

    def send_all(self, message, response_back = False, timeout = None):
        for player in self.clients.keys():
            self.send_to_uuid(player, [2 if response_back else 1, message])

    def send_all_in_game(self, message, response_back = False, timeoutt = None):
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
                    self.response_back_event.wait(timout = start_time + timeoutt - time.time() if timeoutt is not None else None)
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


    def send_to_uuid(self, uuid, message, response_back = False):
        self.send_client(self.clients[uuid][0],message)

    def send_client(self, connection_socket, message):

        if type(message) != list:
            message = [message]
        if message[-1] != END_TOKEN:
            message.append(END_TOKEN)
        for item in message:
            #print(item)
            connection_socket.sendall(struct.pack("!I",item) if utils.is_type_number(item) else item.encode())
        self.debug_send(message)






    def move_to_lobby(self, uuid, reason = ""):
        if uuid in self.in_game:
            self.in_lobby.add(uuid)
            self.in_game.remove(uuid)
        self.send_to_uuid(uuid, f"You have been moved to the lobby. {reason}")

    def receiving(self, client_socket): #get data from client x
        while True:
            text = b""
            end_token = False
            while not end_token:
                text += client_socket.recv(self.BUFFER_SIZE)
                if text[-len(END_TOKEN.encode()):] == END_TOKEN.encode():  # look if the received ends with END_TOKEN token
                    end_token = True
            self.receive_queue.put(text[:-len(END_TOKEN.encode())])
            if DEBUG_SERVER: print("Server debug (receiving): ",struct.unpack("!I", text[:4]),text[4:].decode())

    #before threading
    """def get_player_connections(self, server_socket):
        start_time = time.time()
        while start_time + 60 > time.time():
            connection_socket, client_addr = server_socket.accept()
            self.get_uuid()
            self.clients[] = connection_socket
            print(f'New client with address {client_addr}')"""
    def ask_user_name(self, client_socket):
        #self.send_client(client_socket, [3,'What is your session username?'])
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
            print(f"self.registering_received: {self.registering_received}, and registered: {registered}")
            uuid = self.database.get_uuid_data(self.registering_received if registered else None)

            #if not registered:
            print(f"The uuid is {uuid}")
            self.send_client(client_socket, [3,uuid])

            user_name = self.ask_user_name(client_socket)


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

            if DEBUG_SERVER: print(f"Server: {'new' if not registered else ''} User {self.registering_received} logged in as {user_name}, with uuid {uuid}")


    def treating_queue(self):
        while True:
            request = self.receive_queue.get(block=True)
            match struct.unpack('!I',request[:4])[0]:
                case 1:
                    continue
                case 2:
                    while self.response_back_event.is_set():
                        continue #wait until response back is consumed by request_user_input()
                    self.response_back = (request[4:36+4], request[36+4:])   # 4 token, 36 is len of uuid. final (uuid, user_message)
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


    def request_user_input_w_soket(self, user_soket, message, timout = None):
        pass

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
        #with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_soket = server_socket
        server_socket.bind((self.host, self.port))
        server_socket.listen(self.player_allowed)
        #server_socket.settimeout(self.TIMEOUT)
        print('Server is ready')  # done with step 1

        #self.get_player_connections(server_socket)
        connections = threading.Thread(target=self.get_player_connections, args=[server_socket]) #gets new connections
        #self.receiving(server_socket)
        #receiving = threading.Thread(target=self.receiving) #Get TCP messages sent by clients
        treat_received_messages = threading.Thread(target=self.treating_queue)
        connections.start()
        treat_received_messages.start()
        #while self.server_open:
            #continue



#to test
#Connections more that self.player_allowed
#User takes forever to input username. causing blockage in new connections

if __name__ == '__main__':
    server = Server()
