import uuid
from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
import queue
import struct

SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 12000
BUFFER_SIZE = 8192

END_TOKEN = "<[{.o___o.}]>"


#local utils to avoid multiple files on client side
def utils_is_type_number(x):
    return type(x)==float or type(x)==int

def utils_is_int(x):
    try:
        return int(x) == float(x)
    except ValueError:
        return False


class Client:
    def __init__(self):
        self.uuid = None
        self.load_uuid()
        self.receive_queue = queue.Queue()

        self.user_random_input = threading.Event() #random because this is not required input (not requested)

        self.start_client()


    def receiving(self): #get data from client x
        text = ""
        end_token = False
        while not end_token:
            text += self.client_socket.recv(BUFFER_SIZE)
            if text[-len(END_TOKEN.encode()):] == END_TOKEN.encode():  # look if the received ends with END_TOKEN token
                end_token = True
        self.receive_queue.put(text[:-len(END_TOKEN.encode())])

    def send(self, message):
        if type(message) != list or type(message) != tuple:
            message = [message]
        if message[-1] != END_TOKEN:
            message.append(END_TOKEN)
        for item in message:
            self.client_socket.sendall(struct.pack(item) if utils_is_type_number(item) else item.encode())

    def get_valid_username(self):
        valid = False
        while not valid:
            valid = True
            user_name = input("What is your username?: ")
            if utils_is_type_number(user_name[0]):
                valid = False
                print("Username cannot start with a number. Try again.", end=" ")


    def get_valid_input(self, input_type):
        """
        input_type. 0 for anything (string), 1 for int. 2 for any nbr type.
        :param input_type:
        :return:
        """
        while True:
            result = input("\033[31m==>\033[0m")
            match input_type:
                case "0":
                    if result: return result
                case "1":
                    if utils_is_int(result): return result
                    print("Invalid input. Expected integer")
                case "2":
                    if utils_is_type_number(result): return result
                    print("Invalid input. Expected a number")
            return result

    def treating_queue(self):
        while True:
            message = self.receive_queue.get(block=True)
            match struct.unpack('!I',message[:4])[0]:
                case 1:
                    print(message[4:].decode())
                case 2:
                    print(message[8:].decode())
                    self.user_random_input.clear()

                    self.send([2,self.get_valid_input(struct.unpack('!I',message[4:8]))])
                    self.user_random_input.set()
                case 3:
                    #print(message[4:].decode(), "3 request sent after connection done") #shouldn't arrive
                    self.send([3, self.get_valid_username()])
                case 4:
                    continue
                case _:
                    print(f"Unrecognized request {struct.unpack('!I',message[:4])[0]} received")

    def load_uuid(self):
        try:
            with open("ID.dat", "r") as file:
                self.uuid = file.readline().strip()
        except FileNotFoundError:
            self.uuid = None

    def store_uuid(self):
        with open("ID.dat", "w") as file:
            file.write(self.uuid)

    def connect(self):
        self.send([3,self.uuid])

        if not uuid:
            self.receiving()
            self.uuid = self.receive_queue.get(True)[4:-len(END_TOKEN.encode())].decode()
            self.store_uuid()

        self.receiving()
        self.treating_queue()


    def user_input(self, token =1):
        while self.user_random_input:
            txt = input(">")
            self.send([token,self.uuid, txt])

    def start_client(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((SERVER_ADDR, SERVER_PORT))

        self.connect()

        receiving = threading.Thread(target=self.receiving)  # gets new connections

        treat_received_messages = threading.Thread(target=self.treating_queue)

        self.inputing = threading.Thread(target=self.user_input)

        receiving.isDaemon()
        treat_received_messages.isDaemon()
        self.inputing.isDaemon()

        receiving.start()
        treat_received_messages.start()
        self.inputing.start()

        #client_socket.sendall(text.encode())

        #modified_text = client_socket.recv(BUFFER_SIZE).decode()



if __name__ == '__main__':
    client = Client()