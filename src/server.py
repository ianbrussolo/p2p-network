import socket
import threading
from message import MessageHandler


class PeerServer:
    def __init__(self, address, port, peer_node):
        self.address = address
        self.port = int(port)
        self.peer_node = peer_node
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_handler = MessageHandler(peer_node)

    def start(self):
        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {self.address}:{self.port}")

        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(
                target=self.handle_client, args=(client_socket, client_address)
            ).start()

    def handle_client(self, client_socket, client_address):
        with client_socket:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                self.message_handler.process_message(data.strip(), client_socket)

    def close(self):
        self.server_socket.close()
