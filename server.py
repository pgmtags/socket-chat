"""
By Sudhanshu Vishnoi, Update by AndrijZyn
Python socket based CLI multi-client chat (server)
    makes use of SELECT multiplexing to multiplex multiple clients
- Proper error handling and messages
- can send to all users or a single user
- create chat rooms
- keeps track of usernames and identifiers
"""

import asyncio
import socket
from select import select
from colorama import init, Fore

init(autoreset=True)


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

    async def init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        self.network["default"]["connections"].append(self.server_socket)
        self.network["default"]["names"].append("<server>")

        print(f"{Fore.LIGHTYELLOW_EX}Server has been started in {self.HOST}:{self.PORT}")

        loop = asyncio.get_running_loop()
        while True:
            all_connections = []
            for key in self.network:
                all_connections += self.network[key]["connections"]
            read_sockets, _, _ = await loop.run_in_executor(None, select, all_connections, [], [])

            for sock in read_sockets:
                if sock == self.server_socket:
                    await self.handle_new_connection()
                else:
                    await self.handle_client_message(sock)

    async def remove_client(self, sock):
        for group in self.network:
            if sock in self.network[group]["connections"]:
                i = self.network[group]["connections"].index(sock)
                client_name = self.network[group]["names"][i]
                print((f"{Fore.LIGHTRED_EX}{client_name} from [{group}] "
                       f"<{sock.getpeername()[0]}:{sock.getpeername()[1]}> went offline."))
                await self.broadcast(group, sock, f"{Fore.LIGHTRED_EX}{client_name} from "
                                                  f"<{sock.getpeername()[0]}:{sock.getpeername()[1]}> went offline.",
                                     is_info=True)
                del self.network[group]["connections"][i]
                del self.network[group]["names"][i]
                break
        sock.close()

    async def handle_new_connection(self):
        loop = asyncio.get_running_loop()
        sockfd, addr = await loop.sock_accept(self.server_socket)
        await self.send_rooms_list(sockfd)

        group = await loop.sock_recv(sockfd, 32)
        group = group.strip().decode()
        if group == "":
            sockfd.close()
            return
        elif group not in self.network.keys():
            self.create_new_group(group)

        client_name = await loop.sock_recv(sockfd, 32)
        client_name = client_name.strip().decode()
        if client_name == "":
            sockfd.close()
            return
        elif client_name not in self.network[group]["names"]:
            await self.handle_new_client(sockfd, group, client_name)
        else:
            await loop.sock_sendall(sockfd, "SERVER_FAIL".encode())
            sockfd.close()

    async def send_rooms_list(self, sockfd):
        rooms_list = ""
        for group in self.network.keys():
            number_of_members_in_room = len(self.network[group]["connections"])
            if group == "default":
                number_of_members_in_room -= 1  # exclude server
            rooms_list += f"{group} <{number_of_members_in_room}>::"
        rooms_list = rooms_list[:-2]
        await asyncio.get_running_loop().sock_sendall(sockfd, rooms_list.encode())

    def create_new_group(self, group):
        self.network[group] = {
            "connections": [],
            "names": []
        }

    async def handle_new_client(self, sockfd, group, client_name):
        addr = sockfd.getpeername()
        self.network[group]["names"].append(client_name)
        self.network[group]["connections"].append(sockfd)

        print(f"{Fore.LIGHTRED_EX}{client_name} was connected to "
              f"[{group}] from <{addr[0]}:{addr[1]}>")

        await self.broadcast(group, sockfd, f"{Fore.LIGHTRED_EX}{client_name} was connected to "
                                            f"from group <{addr[0]}:{addr[1]}>", is_info=True)
        await asyncio.get_running_loop().sock_sendall(sockfd, "SERVER_INFO".encode())

    async def handle_client_message(self, sock):
        try:
            data = await asyncio.get_running_loop().sock_recv(sock, self.RECV_BUFFER)
            if not data:
                await self.remove_client(sock)
                return
        except (socket.error, ConnectionResetError) as e:
            print(f"Error receiving data from {sock.getpeername()}: {e}")
            await self.remove_client(sock)
            return

        try:
            group, message = data.decode().split(self.separator, 1)
        except ValueError:
            print(f"Invalid message format from {sock.getpeername()}")
            await self.remove_client(sock)
            return

        if "LIST" in message:
            await self.send_list(group, sock)
        else:
            await self.broadcast(group, sock, message)

    async def send_list(self, group, requestor):
        names = self.network[group]["names"]
        connections = self.network[group]["connections"]

        list_str = ""
        for name, addr in zip(names, connections):
            host, port = addr.getpeername()
            list_str += f"{name} <{host}:{port}>::"
        await asyncio.get_running_loop().sock_sendall(requestor, list_str[:-2].encode())

    async def broadcast(self, group, sender, message, is_info=False):
        sender_name = "SERVER_INFO" if is_info else self.network[group]["names"][
            self.network[group]["connections"].index(sender)]
        message = f"{sender_name}{self.separator}{message}".encode()

        for server_socket in self.network[group]["connections"]:
            if server_socket != self.server_socket and server_socket != sender:
                try:
                    await asyncio.get_running_loop().sock_sendall(server_socket, message)
                except BrokenPipeError:
                    await self.remove_client(server_socket)


async def main():
    server = ChatServer(port=5000)
    asyncio.get_running_loop()

    try:
        await server.init()
    except asyncio.CancelledError:
        pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit, OSError):
        print("Server has been stopped")
