import uuid
from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
from unittest import case

#from blackjack import Blackjack
#from traceback import print_tb
#from xml.dom.domreg import registered

from database import Database
import struct
#import utils
#import queue

END_TOKEN = "<[{.o___o.}]>"

DEBUG_SERVER = True


def utils_is_type_number(item):
    return type(item) is int



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

BUFFER_SIZE = 8192
PORT = 12000
HOST = '0.0.0.0'#'127.0.0.1'

class Server:
    server_ports = set()

    User_connected = set()
    User_connected_lock = threading.Lock()

    def __init__(self, player_allowed=100, TIMEOUT = 30, rule_function = None):
        self.game_rules = rule_function
        self.game_state = "Waiting"
        self.player_allowed = player_allowed
        self.TIMEOUT = TIMEOUT

        #all the next block serve the same function of handling received messages via different threads(#00000000 mark end of block)
        #tasks received
        #self.receive_queue = queue.Queue()
        #self.receive_queue_lock = threading.Lock()

        self.database = Database() # handles users data long term

        #players
        self.clients = dict()   #has volatile data. stores sockets {uuid: [client_socket, thread, user_name]}. thread is the thread responsible for receiving this user's input
        self.in_game = set()   #players in the game
        self.in_lobby = set()   #player waiting for game to end

        self.start_server()


    def start_server(self):
        self.server_socket = socket(AF_INET, SOCK_STREAM)

        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(self.player_allowed)

        print('Server is ready')  # done with step 1

        #self.get_player_connections(server_socket)
        connections = threading.Thread(target=self.get_player_connections, daemon=True) #gets new connections
        connections.start()

        #self.receiving(server_socket)
        #receiving = threading.Thread(target=self.receiving) #Get TCP messages sent by clients
        #treat_received_messages = threading.Thread(target=self.treating_queue)


        #treat_received_messages.isDaemon()


        #treat_received_messages.start()


    def get_player_connections(self): #thread that runs forever to get new connections
        while True:
            client_socket, client_addr = self.server_socket.accept()

            uuid = self.receive(client_socket)
            uuid = self.database.is_uuid_else_generate(uuid if uuid else None)


            self.send_to_client(client_socket, uuid)

            if uuid in self.in_game:
                self.clients[uuid][0] = client_socket
                time.sleep(0.5)
                continue

            self.clients[uuid] = [client_socket]
            if DEBUG_SERVER: print(f"Server: user logged in with uuid {uuid}. will wait for Username")



            get_username = threading.Thread(target=self.get_username, args=(client_socket,uuid), daemon=True)
            get_username.start()


    """def receive(self, client_socket): #get data from client x
        text = b""
        end_token = False
        while not end_token:
            text += client_socket.recv(BUFFER_SIZE)
            if text[-len(END_TOKEN.encode()):] == END_TOKEN.encode():  # look if the received ends with END_TOKEN token
                end_token = True
        if DEBUG_SERVER: print("Server debug (receiving): ",text.decode())
        return text[:-len(END_TOKEN.encode())].decode()"""

    def receive(self, client_socket, timeout=None):
        previous_timeout = client_socket.gettimeout()

        if timeout is not None:
            client_socket.settimeout(timeout)

        try:
            text = b""
            end_token = END_TOKEN.encode()

            while not text.endswith(end_token):
                chunk = client_socket.recv(BUFFER_SIZE)

                if not chunk:
                    raise ConnectionError("Client disconnected")

                text += chunk

            if DEBUG_SERVER:
                print("Server debug (receiving): ", text.decode())

            return text[:-len(end_token)].decode()

        finally:
            if timeout is not None:
                client_socket.settimeout(previous_timeout)



    def send_to_client(self, connection_socket, message):

        if type(message) != list:
            message = [message]
        if message[-1] != END_TOKEN:
            message.append(END_TOKEN)
        try:
            for item in message:
                #print(item)
                connection_socket.sendall(struct.pack("!I",item) if utils_is_type_number(item) else item.encode())

            self.debug_send(message)
        except ConnectionAbortedError:
            if DEBUG_SERVER: print("connection aborted to user ??? cannot send: ", message )
            return False
        return True


    def get_username(self, client_socket, uuid):
        self.send_to_client(client_socket, [3,'What is your session username?'])
        username = self.receive(client_socket)
        self.clients[uuid].append(username)

        if DEBUG_SERVER: print(f"SERVER DEBUG: uuid {uuid} is username {username}")

        if self.game_rules: self.send_to_client(client_socket, [1, self.game_rules()])

        if self.game_state == "Waiting":
            self.in_game.add(uuid)
        else:
            self.in_lobby.add(uuid)

        if DEBUG_SERVER:
            print("Registered:", uuid)
            print("Current in_game:", self.in_game)
            print("Current in_lobby:", self.in_lobby)




    def debug_send(self, what_sent):
        if DEBUG_SERVER : print(f"debug server (send): {what_sent}")

    """def receive_from_uuid(self, uuid):
        return self.receive(self.clients[uuid][0])"""

    def receive_from_uuid(self, uuid, timeout=None):
        return self.receive(self.clients[uuid][0], timeout)

    def send_to_uuid(self, uuid, message):
        if not self.send_to_client(self.clients[uuid][0],message) and self.game_state == "Waiting":
            self.disconnect_user(uuid, False)


    def send_all(self, send_to_uuid: set ,message, timeout = None, balance = None):
        uuids = list(send_to_uuid)
        for player_uuid in uuids:
            self.send_to_uuid(player_uuid, message + ([] if balance is None else [" . You have ",str(balance[player_uuid]), " Tokens."]))

        if message[0] == 2: #2 because wait for answer back from user #can be recurssive
            """self.server_socket.settimeout((timeout if timeout else self.TIMEOUT)+1)"""
            response = dict()
            missed_responses = {} #those who did not send a response back in time

            def thread_get_all_input(player_uuid, store):
                try:
                    store[player_uuid] = self.receive_from_uuid(player_uuid, (timeout if timeout is not None else self.TIMEOUT) + 1)
                except OSError:
                    store[player_uuid] = None
                    #self.disconnect_user(player_uuid)

            thread_list = set()
            for player_uuid in uuids:
                thread_list.add(threading.Thread(target=thread_get_all_input, args=(player_uuid,response))) # gets new connections
            for thread in thread_list:
                thread.start()
            for thread in thread_list:
                thread.join()

            if DEBUG_SERVER: print(f"SERVER DEBUG (sendall): responses = {response})")
            #player did not respond back will have {uuid: ""} as answer
            return response

    def move_to_lobby(self, uuid, reason = ""):
        if uuid not in self.clients:
            return
        if uuid in self.in_game:
            self.in_lobby.add(uuid)
            self.in_game.remove(uuid)
            self.send_to_uuid(uuid, [1, f"You have been moved to the lobby. {reason}"])


    def send_all_in_game(self,message, remove: set  = None):
        if remove is None:
            remove = set()
        self.send_all(self.in_game-remove, [1]+message)


    def request_user_input(self, uuid, message, timout = None):
        return self.send_all({uuid}, message, timout)[uuid]












    #before threading
    """def get_player_connections(self, server_socket):
        start_time = time.time()
        while start_time + 60 > time.time():
            connection_socket, client_addr = server_socket.accept()
            self.get_uuid()
            self.clients[] = connection_socket
            print(f'New client with address {client_addr}')"""


    def get_uuid(self, client_socket):
        pass





    def treating_queue(self):
        while True:
            request = self.receive_queue.get(block=True)
            match struct.unpack('!I',request[:4])[0]:
                case 1:
                    continue
                case 2:
                    while self.response_back_event.is_set():
                        continue #wait until response back is consumed by request_user_input()
                    self.response_back = (request[4:36+4].decode(), request[36+4:].decode())   # 4 token, 36 is len of uuid. final (uuid, user_message)
                    if self.ignore[self.response_back[0]] == 0:
                        self.response_back_event.set()
                    elif self.ignore[self.response_back[0]]> 0:
                        self.ignore[self.response_back[0]] -= 1
                    else:
                        print(f"self.ignore of uuid({self.response_back[0].decode()}) equal to {self.ignore[self.response_back[0].decode()]}. not supposed to be negative")

                case 3:
                    match struct.unpack('!I',request[4:8])[0]:
                        case 1:
                            self.registering_received = request[8:].decode()
                            self.registering_lock.release()
                        case 2:
                            self.clients[request[8:8+36].decode()].append(request[8+36:].decode())
                            if DEBUG_SERVER: print(f"uuid {request[8:8+36].decode()} is username {request[8+36:].decode()}")
                            if self.game_state == "Waiting":
                                self.in_game_lock.acquire()
                                self.in_game.add(request[8:8+36].decode())
                                self.in_game_lock.release()
                            else:
                                self.in_lobby_lock.acquire()
                                self.in_lobby.add(request[8:8 + 36].decode())
                                self.in_lobby_lock.release()
                            if self.game_rules: self.send_to_uuid(request[8:8+36].decode(), [1, self.game_rules()])
                case 4:
                    continue
                case _:
                    print(f"Unrecognized request {struct.unpack('!I',request[:4])[0]} received")


    def disconnect_user(self, uuid, print = True):
        client = self.clients.pop(uuid, None)
        self.in_game.discard(uuid)
        self.in_lobby.discard(uuid)

        if client:
            if print:
                try:
                    self.send_to_client(client[0], ["You got disconnected!"])
                except OSError:
                    pass

            client[0].close()












#to test
#Connections more that self.player_allowed
#User takes forever to input username. causing blockage in new connections

if __name__ == '__main__':
    server = Server()
