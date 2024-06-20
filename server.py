"""
By Sudhanshu Vishnoi, Update by AndrijZyn
Python socket based CLI multi-client chat (server)
    makes use of SELECT multiplexing to multiplex multiple clients
- Proper error handling and messages
- can send to all users or a single user
- create chat rooms
- keeps track of usernames and identifiers
"""

import socket
import select
from colorama import init, Fore, Style

init(autoreset=True)  # Initialize colorama


class ChatServer:
    def __init__(self, host="localhost", port=5000):
        self.network = {
            "default": {
                "connections": [],
                "names": []
            }
        }
        self.RECV_BUFFER = 4096
        self.HOST = host
        self.PORT = port
        self.server_socket = None
        self.separator = "::"

    def init(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.HOST, self.PORT))
            self.server_socket.listen(5)

            self.network["default"]["connections"].append(self.server_socket)
            self.network["default"]["names"].append("<server>")

            print(f"{Fore.LIGHTYELLOW_EX}Server has been starter in {self.HOST}:{self.PORT}{Style.RESET_ALL}")

            while True:
                all_connections = []
                for key in self.network:
                    all_connections += self.network[key]["connections"]
                read_sockets, _, _ = select.select(all_connections, [], [])

                for sock in read_sockets:
                    if sock == self.server_socket:
                        self.handle_new_connection()
                    else:
                        self.handle_client_message(sock)
        finally:
            return 0

    def remove_client(self, sock):
        for group in self.network:
            if sock in self.network[group]["connections"]:
                i = self.network[group]["connections"].index(sock)
                client_name = self.network[group]["names"][i]
                msg_notification = (f"{Fore.LIGHTRED_EX}{client_name} from [{group}] "
                                    f"<{sock.getpeername()[0]}:{sock.getpeername()[1]}> went offline.{Style.RESET_ALL}")
                print(msg_notification)
                self.broadcast(group, sock, msg_notification, is_info=True)
                del self.network[group]["connections"][i]
                del self.network[group]["names"][i]
                sock.close()  # close the socket
                break
        else:
            sock.close()  # close the socket if it's not found in any group

    def handle_new_connection(self):
        sockfd, addr = self.server_socket.accept()
        self.send_rooms_list(sockfd)

        group = sockfd.recv(32).strip().decode()
        if group == "":
            return
        elif group not in self.network.keys():
            self.create_new_group(group)

        client_name = sockfd.recv(100).strip().decode()
        if client_name == "":
            return
        elif client_name not in self.network[group]["names"]:
            self.handle_new_client(sockfd, group, client_name)
        else:
            sockfd.send("SERVER_FAIL".encode() + self.separator.encode() + "Cannot have same name.".encode())

    def send_rooms_list(self, sockfd):
        rooms_list = ""
        for group in self.network.keys():
            number_of_members_in_room = len(self.network[group]["connections"])
            if group == "default":
                number_of_members_in_room -= 1  # exclude server
            rooms_list += f"{group} <{number_of_members_in_room}>::"
        rooms_list = rooms_list[:-2]
        sockfd.send(rooms_list.encode())

    def create_new_group(self, group):
        self.network[group] = {
            "connections": [],
            "names": []
        }

    def handle_new_client(self, sockfd, group, client_name):
        addr = sockfd.getpeername()
        self.network[group]["names"].append(client_name)
        self.network[group]["connections"].append(sockfd)
        msg_notification = (f"{Fore.LIGHTRED_EX}{client_name} was connected to "
                            f"[{group}] from <{addr[0]}:{addr[1]}>{Style.RESET_ALL}")
        print(msg_notification)
        self.broadcast(group, sockfd, msg_notification, is_info=True)
        sockfd.send(f"SERVER_INFO{self.separator}Welcome.".encode())  # Need fix that

    def handle_client_message(self, sock):
        try:
            data = sock.recv(self.RECV_BUFFER)
            if not data:
                self.remove_client(sock)
                return

            group, message = data.decode().split(self.separator, 1)
            if "LIST" in message:
                self.send_list(group, sock)
            else:
                self.broadcast(group, sock, message)

        except (socket.error, ValueError, BrokenPipeError) as e:
            print(f"Error receiving or processing data from {sock.getpeername()}: {e}")
            self.remove_client(sock)

        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            self.remove_client(sock)

    def send_list(self, group, requestor):
        names = self.network[group]["names"]
        connections = self.network[group]["connections"]

        list_str = ""
        for name, addr in zip(names, connections):
            host, port = addr.getpeername()
            list_str += f"{name} <{host}:{port}>::"
        requestor.send(list_str[:-2].encode())

    def broadcast(self, group, sender, message, is_info=False):
        sender_name = "SERVER_INFO" if is_info else self.network[group]["names"][
            self.network[group]["connections"].index(sender)]
        message = f"{sender_name}{self.separator}{message}".encode()

        for server_socket in self.network[group]["connections"]:
            if server_socket != self.server_socket and server_socket != sender:
                try:
                    server_socket.sendall(message)
                except BrokenPipeError:
                    self.remove_client(server_socket)


if __name__ == '__main__':
    server = ChatServer(port=5000)
    server.init()
