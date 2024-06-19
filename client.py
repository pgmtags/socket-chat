import sys
import select
import socket
from colorama import Fore, Style

"""
By Sudhanshu Vishnoi, Update by AndrijZyn
Python socket based CLI multi-client chat (client)
    makes use of SELECT multiplexing to multiplex user input and responses
- Join existing chat rooms or create your own chat room
- Receive / Send messages by your username
- Send messages to specific person
- Colored terminal output
"""

# TODO: add the ability to change the lobby. Create func 'change_lobby'
# TODO: fix queue in setup_chat_room()
# TODO: give the ability to write emoji in the console, or make a command that will convert certain codes into emoji,
#  the list of codes will be displayed behind the command
# TODO: Add user login & create DB with User information(Password, user,
#       (maybe)ID, bonusKey (If i'll add ID user to restore the "Name"))
#       At the moment I am unable to fix one thing when trying to implement this function (


# Emoji's
problem = "\N{anger symbol}... \n"
angry = " \N{angry face}"


class ChatClient:
    RECV_BUFFER = 4096
    separator = '::'
    group = "default"
    username = ""
    helpMsg = ("Available commands:"
               "\nHELP - Show this message\nCLEAR - Clear the screen\nLIST - Display all users\nEXIT - Exit the chat")

    def __init__(self, host_, port_):
        self.host = host_
        self.port = port_
        self.s = None
        self.timeout = 0.1

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(self.timeout)
            self.s.connect((self.host, self.port))
            print("Connected to server!")
        except socket.timeout:
            print(problem + "IDK where to dock" + angry)
            sys.exit(0)
        except socket.error as e:
            print(problem + f"Connection error: {e}")
            sys.exit(1)

    def disconnect(self):
        print("Disconnecting from server...")
        if self.s:
            self.s.close()
        sys.exit(0)

    @staticmethod
    def prompt():
        sys.stdout.write(f"{Fore.GREEN}{Style.BRIGHT}> {Fore.RESET}")
        sys.stdout.flush()

    @staticmethod
    def clear_current_line():
        sys.stdout.write("\033[K")
        sys.stdout.flush()

    def print_list(self, title, data):
        if not data:
            print(f"{title}: No data received.")
            return
        print(f"{title}:")
        for item in data.split(self.separator):
            print(f"- {item}")

    def handle_incoming_message(self, data):
        if not data:
            self.disconnect()
        else:
            try:
                dt = data.split(self.separator, 1)
                if len(dt) < 2:
                    print(f"Malformed message: {data}")
                    return
                name, msg = dt
                self.clear_current_line()

                if name == "SERVER_INFO":
                    sys.stdout.write(Fore.YELLOW + Style.BRIGHT)
                    sys.stdout.write("INFO> ")
                elif name == "PEOPLE_ONLINE":
                    self.print_list("PEOPLE ONLINE", msg)
                else:
                    sys.stdout.write(Fore.CYAN + Style.BRIGHT)
                    sys.stdout.write(f"{name}> ")

                sys.stdout.write(Fore.RESET)
                sys.stdout.write(f"{msg}\n")
            except Exception as e:
                print(problem + f"Error processing message: {e}")

    def handle_user_input(self, msg):
        if msg == "EXIT":
            self.disconnect()
        elif msg == "CLEAR":
            print("\x1b[2J\x1b[H")
            self.clear_current_line()
        elif msg == "HELP":
            print(self.helpMsg)
        elif msg == "LIST":
            self.s.send((self.group + self.separator + "LIST").encode())
        elif len(msg) > 0:
            try:
                self.s.send((self.group + self.separator + msg).encode())
            except socket.error as e:
                print(problem + f"Send error: {e}")
                self.disconnect()

    def setup_chat_room(self):
        try:
            data = self.s.recv(self.RECV_BUFFER).decode('utf-8')
            self.print_list(f"{Fore.GREEN}CHAT ROOMS", data)
            groupName = input(f"{Fore.MAGENTA}Join a Chat Room or Create New: {Fore.YELLOW}").replace(" ", "")
            if groupName:
                self.group = groupName
            self.s.send(self.group.encode())
        except TimeoutError:
            print("Please, Wait for the other person to validate")  # Need fix queue
            sys.exit(0)

    def get_username(self):
        while not self.username:
            self.username = input(f"{Fore.MAGENTA}Enter your Name: {Fore.YELLOW}").replace(" ", "")
        print(Fore.RESET)
        self.s.send(self.username.encode())

    def handle_first_connection(self):
        firstConnResponse = self.s.recv(self.RECV_BUFFER).decode()
        if f"SERVER_FAIL{self.separator}" in firstConnResponse:
            print(f"{Fore.RED}{Style.BRIGHT}ERROR> Cannot have same names{Fore.RESET}")
            self.disconnect()
        else:
            print(f"{Fore.YELLOW}{Style.BRIGHT}INFO>{Fore.YELLOW} "
                  f"Connected to host. Start sending messages.{Fore.RESET}")
            print(self.helpMsg)
            print(f"{Fore.MAGENTA}Joined {Fore.YELLOW}{self.group}{Fore.MAGENTA} "
                  f"group as {Fore.YELLOW}{self.username}{Fore.RESET}")

    def run(self):
        self.connect()
        self.setup_chat_room()
        self.get_username()
        self.handle_first_connection()

        while True:
            self.prompt()
            socket_list = [sys.stdin, self.s]
            read_sockets, _, _ = select.select(socket_list, [], [])
            for sock in read_sockets:
                if sock == self.s:
                    try:
                        data = self.s.recv(self.RECV_BUFFER).decode('utf-8')
                        if not data:
                            self.disconnect()
                        self.handle_incoming_message(data)
                    except socket.error as e:
                        print(problem + f"Receive error: {e}")
                        self.disconnect()
                else:
                    msg = sys.stdin.readline().strip()
                    self.handle_user_input(msg)


if __name__ == "__main__":
    client = ChatClient("localhost", 5000)
    client.run()
