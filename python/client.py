"""
By Sudhanshu Vishnoi
Update by AndrijZyn
Python socket based CLI multi-client chat (client)
    makes use of SELECT multiplexing to multiplex user input and responses
- Join existing chat rooms or create your own chat room
- Receive / Send messages by your username
- Send messages to specific person
- Colored terminal output
"""


# TODO: add the ability to change the lobby. Create func 'change_lobby'
# TODO: add emojis for better output errors & warnings. import emoji (💢 - for warnings)
# TODO: add more except's for better stability.
#       KeyboardInterrupt,  Exception, socket.error, ValueError, BrokenPipeError & etc...
# TODO: rewrite coloring. Create pallete colors for better using
#

"""
 self.username = input("{}Enter your Name: {}".format(Fore.MAGENTA, Fore.YELLOW)).replace(" ", "")
 TODO: rewrite format() : ^ to {Fore.MAGENTA}Enter your Name: | ...
"""


import select
import socket
import sys

from colorama import init, Fore, Style

init(autoreset=True)  # Initialize colorama


def disconnect():
    print(Fore.RED + Style.BRIGHT + 'Disconnected from chat server\n')
    sys.exit(0)


def clear_current_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


class ChatClient:
    def __init__(self, host="localhost", port=5000):
        self.HOST = host
        self.PORT = port
        self.RECV_BUFFER = 4096
        self.username = ""
        self.group = "default"
        self.separator = "&&&"  # same as of server
        self.helpMsg = """{}
            LIST => to get list of people online\n
            @name => to reply send message to specific person\n
            CLEAR => clear screen\n
            HELP => display this help message\n
            EXIT => exit.
        {}""".format(Fore.MAGENTA, Fore.RESET)

    def prompt(self):
        # prompt for current active user to type message
        clear_current_line()
        print(Fore.GREEN + Style.BRIGHT + self.username + "> " + Fore.RESET, end="")

    def init(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)

        try:
            s.connect((self.HOST, self.PORT))
        except:
            print('Unable to connect')
            sys.exit()

        # set chat room
        self.printList("CHAT ROOMS", s.recv(self.RECV_BUFFER).decode('utf-8'))

        groupName = input("{}Join a Chat Room or Create New: {}".format(Fore.MAGENTA, Fore.YELLOW)).replace(" ", "")
        if groupName != "":
            self.group = groupName

        s.send(self.group.encode())

        # get user's name and send to server
        while self.username == "":
            self.username = input("{}Enter your Name: {}".format(Fore.MAGENTA, Fore.YELLOW)).replace(" ", "")

        print(Fore.RESET)
        s.send(self.username.encode())

        firstConnResponse = s.recv(self.RECV_BUFFER).decode()

        if ("SERVER_FAIL" + self.separator) in firstConnResponse:
            print("{}{}ERROR> Cannot have same names{}".format(Fore.RED + Style.BRIGHT, Fore.RED, Fore.RESET))
            disconnect()
        else:
            print(
                "{}{}INFO>{} Connected to host. Start sending messages.".format(Fore.YELLOW + Style.BRIGHT, Fore.YELLOW,
                                                                                Fore.RESET))
            print(self.helpMsg)
            print("{}Joined {}{}{} group as {}{}{}".format(Fore.MAGENTA, Fore.YELLOW, self.group, Fore.MAGENTA,
                                                           Fore.YELLOW, self.username, Fore.RESET))

        while True:
            self.prompt()
            socket_list = [sys.stdin, s]

            # get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

            for sock in read_sockets:
                # handle incoming message from remote server
                if sock == s:
                    data = s.recv(self.RECV_BUFFER).decode('utf-8')

                    if not data:
                        disconnect()
                    else:
                        # receive user messages
                        # clears self stdin (bug like thingy)
                        try:
                            dt = data.split(self.separator, 1)
                            name = dt[0]
                            msg = dt[1]

                            clear_current_line()

                            if name == "SERVER_INFO":
                                # information
                                sys.stdout.write(Fore.YELLOW + Style.BRIGHT)
                                sys.stdout.write("INFO" + "> ")
                            else:
                                # normal message
                                sys.stdout.write(Fore.CYAN + Style.BRIGHT)
                                sys.stdout.write(name + "> ")

                            sys.stdout.write(Fore.RESET)
                            sys.stdout.write(msg + "\n")

                        except:
                            # other wise show list of users online
                            # not to best way to handle responses
                            self.printList("PEOPLE ONLINE", data)

                # send message
                else:
                    msg = sys.stdin.readline().strip()

                    if msg == "EXIT":
                        disconnect()

                    elif msg == "CLEAR":
                        print("\x1b[2J\x1b[H")

                    elif msg == "HELP":
                        print(self.helpMsg)

                    elif len(msg) > 0:
                        s.send((self.group + self.separator + msg).encode())

    def printList(self, msg, response):
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        print(Fore.YELLOW + "<---- " + msg + " ---->", Fore.RESET)
        for person in response.split("::"):
            print(Fore.GREEN + "*" + Fore.RESET, person)


def main():
    try:
        host = sys.argv[1].split(":")[0]
    except:
        host = input("Host: ")
    try:
        port = int(sys.argv[1].split(":")[1])
    except:
        port = int(input("Port: "))

    client = ChatClient(host=host, port=port)
    client.init()


if __name__ == '__main__':
    main()
