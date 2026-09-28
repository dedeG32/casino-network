import threading

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


def say_hi():
    while True:
        print("HI")

def thread_spam():



def print_error():
    print(IndexError("out of range"))
if __name__ == "__main__":
    #test_async()
    #print_error()
    thread_spam()