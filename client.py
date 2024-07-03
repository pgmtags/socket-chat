import sys
from select import select
import socket
from colorama import init, Fore, Style
from os import system

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
# TODO: fix handle_first_connection
# TODO: make a normal output of names
# TODO: give the ability to write emoji in the console, or make a command that will convert certain codes into emoji,
#  the list of codes will be displayed behind the command
# TODO: Add user login & create DB with User information(Password, user,
#       (maybe)ID, bonusKey (If i'll add ID user to restore the "Name"))
#       At the moment I am unable to fix one thing when trying to implement this function (

#  ./virtualEnv/bin/python3.11

init(autoreset=True)  # Initialize colorama

# Emoji's
PROBLEM_EMOJI = "\N{anger symbol} "
ANGRY_EMOJI = " \N{angry face}"
EMOJI_HAND = "\U0001F44B"


class ChatClient:
    RECV_BUFFER = 4096
    separator = '::'
    group = "default"
    username = ""
    helpMsg = (f"{Fore.GREEN}{Style.BRIGHT}Available commands:{Style.RESET_ALL}"
               f"\nHELP - Show this message\nCLEAR - Clear the screen\nLIST - Display all users\n")

    def __init__(self, host_, port_):
        self.host = host_
        self.port = port_
        self.s = None
        self.timeout = 0.1
        """
        timeout = 0.1 
        
        If the server does not respond for longer than 100 ms, 
        the client will be disconnected
        """

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(self.timeout)
            self.s.connect((self.host, self.port))
            system('clear')
            print(f"{Fore.GREEN}{Style.BRIGHT}You have been connected to the server Home, "
                  f"{Fore.BLUE}select{Fore.GREEN}, or create a new room")
        except socket.timeout:
            print(PROBLEM_EMOJI + "IDK where to dock" + ANGRY_EMOJI)
            sys.exit(0)
        except socket.error as e:
            print(PROBLEM_EMOJI + f"Connection error: {e}")
            sys.exit(1)

    def disconnect(self, status):
        if status == "cork":
            print("Please, Wait for the other person to validate")  # Need fix queue
            sys.exit(0)
        if status == "name":
            print(f"{Fore.RED}{Style.BRIGHT}ERROR> Can't have same names{Fore.RESET}")
            sys.exit(0)
        system('clear')
        print(f"Disconnected {EMOJI_HAND}")
        if self.s:
            self.s.close()
        sys.exit(0)

    def print_list(self, title, data):
        if not data:
            print(f"{title}: No data received.")
            return
        print(f"{title}:")
        for item in data.split(self.separator):
            print(f"- {item}")

    def handle_incoming_message(self, data):
        if not data:
            self.disconnect("main")
        else:
            try:
                dt = data.split(self.separator, 1)
                if len(dt) < 2:
                    print(f"Malformed message: {data}")
                name, msg = dt

                if name == "SERVER_INFO":
                    sys.stdout.write(Fore.YELLOW + Style.BRIGHT)
                    sys.stdout.write(f"{Fore.RED}{Style.BRIGHT}INFO> ")
                elif name == "PEOPLE_ONLINE":
                    self.print_list("PEOPLE ONLINE", msg)
                else:
                    sys.stdout.write(Fore.CYAN + Style.BRIGHT)
                    sys.stdout.write(f"{name}> ")
                sys.stdout.write(Fore.RESET)
                sys.stdout.write(f"{msg}\n")
            except Exception as e:
                print(PROBLEM_EMOJI + f"Error processing message: {e}")

    def handle_user_input(self, msg):
        if msg == "CLEAR":
            system('clear')
        elif msg == "HELP":
            print(self.helpMsg)
        elif msg == "LIST":
            self.s.send((self.group + self.separator + "LIST").encode())
        elif len(msg) > 0:
            try:
                self.s.send((self.group + self.separator + msg).encode())
            except socket.error as e:
                print(PROBLEM_EMOJI + f"Send error: {e}")
                self.disconnect("main")

    def setup_chat_room(self):
        try:
            data = self.s.recv(self.RECV_BUFFER).decode('utf-8')
            self.print_list(f"{Fore.GREEN}CHAT ROOMS", data)
            groupName = input(f"{Fore.MAGENTA}Join a Chat Room or Create New: {Fore.YELLOW}").replace(" ", "")
            if groupName:
                self.group = groupName
            self.s.send(self.group.encode())
        except KeyboardInterrupt:
            self.disconnect("main")
        except TimeoutError:
            self.disconnect("cork")

    def get_username(self):
        while not self.username:
            self.username = input(f"{Fore.MAGENTA}Enter your Name: {Fore.YELLOW}").replace(" ", "")
        print(Fore.RESET)
        self.s.send(self.username.encode())

    def handle_first_connection(self):
        firstConnResponse = self.s.recv(self.RECV_BUFFER).decode()
        if not firstConnResponse:
            print(f"{Fore.RED}{Style.BRIGHT}ERROR> Connection closed by server{Fore.RESET}")
            self.disconnect("main")
        elif f"SERVER_FAIL{self.separator}" in firstConnResponse:
            self.disconnect("name")
        else:
            system('clear')
            print(self.helpMsg)
            print(f"{Fore.MAGENTA}Joined in group {Fore.YELLOW}{self.group}{Fore.MAGENTA}"
                  f" as {Fore.YELLOW}<{self.username}>{Fore.RESET}\n")

    def run(self):
        self.connect()
        self.setup_chat_room()
        self.get_username()
        self.handle_first_connection()

        while True:
            try:
                sys.stdout.write(f"{Fore.GREEN}{Style.BRIGHT}> {Fore.RESET}")
                sys.stdout.flush()
                socket_list = [sys.stdin, self.s]
                read_sockets, _, _ = select(socket_list, [], [])
                for sock in read_sockets:
                    if sock == self.s:
                        try:
                            data = self.s.recv(self.RECV_BUFFER).decode('utf-8')
                            if not data:
                                self.disconnect("main")
                            self.handle_incoming_message(data)
                        except socket.error as e:
                            print(PROBLEM_EMOJI + f"Receive error: {e}")
                            self.disconnect("main")
                    else:
                        msg = sys.stdin.readline().strip()
                        self.handle_user_input(msg)
            except KeyboardInterrupt:
                self.disconnect("main")


if __name__ == "__main__":
    client = ChatClient("localhost", 5000)
    client.run()
