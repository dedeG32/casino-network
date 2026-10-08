import threading
import time

async def quiting():
    while input().lower() != 'quit':
        print(end="")
    exit(0)

def test_async():
    quiting()
    while True:
        a = int(input("first number"))
        b = int(input("first number"))

        print(a+b, "\n")

def print_error():
    print(IndexError("out of range"))


def say_hi():
    while True:
        print("HI")
        time.sleep(1)

def thread_spam():
    thread = threading.Thread(target=say_hi)
    thread.start()
    while True:
        print("Thread started")
        time.sleep(1)

def thread1():
    while True:
        print("Thread s")

def thread_aquire_test():
    lock = threading.Lock()

def is_bool():
    print(bool("0"))

def append_tuple():
    test = tuple()
    test.append(1)

def list_addition():
    print([1,2,3]+[4,5,6,3])
    print({1,2,3}+{4,5,6,1,2})
    print({1:"he",2:"yo"}+{3:"dd", 2:'gg'})
def utils_is_int(x):
    try:
        print(int(x), " == ", float(x))
        return int(x) == float(x)
    except ValueError:
        return False
def empty_str():
    print(bool("             "))
if __name__ == "__main__":
    #test_async()
    #print_error()
    #thread_spam()
    #thread_aquire_test()
    #is_bool()
    #append_tuple()
    #list_addition()
    #print(utils_is_int(1.1))
    empty_str()