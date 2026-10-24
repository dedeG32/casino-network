from socket import socket, AF_INET, SOCK_STREAM
import time
import threading
import struct

SERVER_ADDR = '10.100.32.111'#'192.168.1.205'#'127.0.0.1'
SERVER_PORT = 12000
BUFFER_SIZE = 8192

END_TOKEN = "<[{.o___o.}]>"

DEBUG_CLIENT = False

TIMEOUT = 30

#local utils to avoid multiple files on client side
def utils_is_type_number(x):
    return type(x)==float or type(x)==int

def utils_is_int(x):

    try:
        return int(x) == float(x)
    except ValueError:
        return False

def utils_is_all_space(x):
    return all([i==" " for i in x])


class Client:
    def __init__(self):
        self.uuid = None
        self.load_uuid()
        self.sent_event = threading.Event()

        self.start_client()


    def load_uuid(self):
        try:
            with open("ID.dat", "r") as file:
                self.uuid = file.readline().strip()
        except FileNotFoundError:
            self.uuid = None

    def store_uuid(self):
        with open("ID.dat", "w") as file:
            file.write(self.uuid)

    def start_client(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((SERVER_ADDR, SERVER_PORT))

        #send uuid to retrieve user data in server. or create account in none
        self.send([self.uuid if self.uuid is not None else ""])
        self.uuid = self.receive().decode()

        self.store_uuid()
        if DEBUG_CLIENT: print(f"Client debug (storing uuid): {self.uuid} stored in ID.dat")

        self.main_loop()

    def main_loop(self):
        while True:
            message = self.receive()
            if DEBUG_CLIENT: print(f"Client debug (treating): {struct.unpack('!I', message[:4])}{message[4:].decode()}")
            match struct.unpack('!I', message[:4])[0]:
                case 1:
                    print(message[4:].decode())
                case 2:
                    print(message[8:].decode())
                    input_type = struct.unpack('!I', message[4:8])[0]

                    def read_and_send_input():
                        try:
                            self.send([self.get_valid_input(input_type, True)])
                        except OSError:
                            pass  # Socket closed after timeout

                    threading.Thread(target=read_and_send_input,daemon=True).start()

                    if not self.sent_event.wait(TIMEOUT):
                        print("Timeout!!! You got disconnected.")
                        #self.send("")
                        self.client_socket.close()
                        return

                    self.sent_event.clear()
                    """
                    print(message[8:].decode())
                    #2 is followed by a second token. 0 mean send string. 1: int. 2:number
                    # self.send([self.get_valid_input(struct.unpack('!I', message[4:8])[0])])
                    def send_input(input_type):
                        self.send([self.get_valid_input(input_type, True)])
                    try:
                        threading.Thread(target=send_input, args=(struct.unpack('!I', message[4:8])[0],), daemon=True).start()
                        time.sleep(TIMEOUT)
                        if not self.sent_event.is_set():
                            raise TimeoutError
                        else:
                            self.sent_event.clear()
                            raise TypeError #finish no error
                    except TimeoutError:
                        self.send([""])
                    except TypeError:
                        continue"""
                case 3:
                    print(message[4:].decode())
                    self.send([self.get_valid_input(0)])
                case _:
                    print(f"Unrecognized request {struct.unpack('!I', message[:4])[0]} received")


    def receive(self): #get data from client x
        text = b""
        end_token = False
        while not end_token:
            text += self.client_socket.recv(BUFFER_SIZE)
            if text[-len(END_TOKEN.encode()):] == END_TOKEN.encode():  # look if the received ends with END_TOKEN token
                end_token = True
        if DEBUG_CLIENT: print(f"Client debug (received): {text.decode()}")
        return text[:-len(END_TOKEN.encode())]


    def send(self, message):
        if type(message) != list:
            message = [message]
        if message[-1] != END_TOKEN:
            message.append(END_TOKEN)
        for item in message:
            if DEBUG_CLIENT: print(f"client debug (send): {item}")
            #self.client_socket.sendall(struct.pack("!I",item) if utils_is_type_number(item) else item.encode())
            self.client_socket.sendall(item.encode())


    def get_valid_input(self, input_type, timeout = False):
        """
        input_type. 0 for anything (string), 1 for int. 2 for any nbr type.
        :param input_type:
        :return:
        """
        if DEBUG_CLIENT: print(f"Client debug (get_valid_input) input_type: {input_type}")
        while True:
            result = input("\033[31m==>\033[0m")
            match input_type:
                case 0:
                    if result:
                        if timeout: self.sent_event.set()
                        return result
                case 1:
                    if utils_is_int(result):
                        if timeout: self.sent_event.set()
                        return result
                    print("Invalid input. Expected integer")
                case 2:
                    if utils_is_type_number(result):
                        if timeout: self.sent_event.set()
                        return result
                    print("Invalid input. Expected a number")












if __name__ == '__main__':
    client = Client()