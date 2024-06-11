import socket


class MessageHandler:
    def __init__(self, peer_node):
        self.peer_node = peer_node

    def send_hello(self, neighbor):
        self.send_message(
            f"{self.peer_node.address}:{self.peer_node.port} {self.peer_node.sequence_number} 1 HELLO\n",
            neighbor,
        )
        self.peer_node.sequence_number += 1

    def send_message(self, message, neighbor):
        try:
            neighbor_address, neighbor_port = neighbor.split(":")
            with socket.create_connection(
                (neighbor_address, int(neighbor_port))
            ) as sock:
                log(f"Encaminhando mensagem {message.strip()} para {neighbor}")
                sock.sendall(message.encode())
                response = sock.recv(1024).decode().strip()
                if response == "HELLO_OK":
                    log(f"Envio feito com sucesso: {message.strip()}")
                else:
                    log(f"Erro ao enviar mensagem: {message.strip()}")
        except Exception as e:
            log(f"Erro ao conectar-se ao vizinho {neighbor}: {e}")

    def process_message(self, message, client_socket):
        log(f"Recebido: {message}")
        parts = message.split()
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        operation = parts[3]

        if operation == "HELLO":
            self.handle_hello(origin, client_socket)
        elif operation == "SEARCH":
            self.handle_search(parts, client_socket)
        elif operation == "VAL":
            self.peer_node.stats.record_hop(parts[4], int(parts[7]))
            log(f"Valor encontrado! Chave: {parts[5]} valor: {parts[6]}")
        elif operation == "BYE":
            self.handle_bye(origin)

    def handle_hello(self, origin, client_socket):
        if origin not in self.peer_node.neighbors:
            self.peer_node.neighbors.append(origin)
            log(f"Adicionando vizinho na tabela: {origin}")
        else:
            log(f"Vizinho já está na tabela: {origin}")
        client_socket.sendall(b"HELLO_OK\n")

    def handle_search(self, parts, client_socket):
        origin = parts[0]
        method = parts[4]
        key = parts[6]
        if method == "FL":
            strategy = FloodingSearchStrategy(self.peer_node)
        elif method == "BP":
            strategy = DepthFirstSearchStrategy(self.peer_node)
        elif method == "RW":
            strategy = RandomWalkSearchStrategy(self.peer_node)
        self.peer_node.search_context.set_strategy(strategy)
        self.peer_node.search_context.search(key, parts, client_socket)

    def handle_bye(self, origin):
        log(f"Mensagem recebida: BYE de {origin}")
        if origin in self.peer_node.neighbors:
            self.peer_node.neighbors.remove(origin)
            log(f"Removendo vizinho da tabela: {origin}")
