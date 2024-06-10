import socket
import sys
import threading
import random
import statistics

class PeerNode:
    def __init__(self, address, port, neighbors_file=None, key_value_file=None):
        self.address = address
        self.port = int(port)
        self.neighbors = []
        self.key_value_store = {}
        self.sequence_number = 0
        self.ttl_default = 100
        self.seen_messages = set()
        self.depth_search_info = {}

        # Estatísticas
        self.stats = {
            'flooding': {'count': 0, 'hops': []},
            'random_walk': {'count': 0, 'hops': []},
            'depth_search': {'count': 0, 'hops': []}
        }

        if neighbors_file:
            self.load_neighbors(neighbors_file)
        if key_value_file:
            self.load_key_values(key_value_file)

        self.start_server()
        self.show_menu()

    def load_neighbors(self, neighbors_file):
        with open(neighbors_file, 'r') as file:
            for line in file:
                neighbor = line.strip()
                print(f"Tentando adicionar vizinho {neighbor}")
                if self.send_hello(neighbor):
                    self.neighbors.append(neighbor)
                    print(f"Vizinho {neighbor} adicionado com sucesso")
                else:
                    print(f"Erro ao adicionar vizinho {neighbor}")

    def load_key_values(self, key_value_file):
        with open(key_value_file, 'r') as file:
            for line in file:
                key, value = line.strip().split()
                self.key_value_store[key] = value

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {self.address}:{self.port}")

        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        with client_socket:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                self.process_message(data.strip(), client_socket)

    def process_message(self, message, client_socket):
        print(f"Recebido: {message}")
        parts = message.split()
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        operation = parts[3]

        if operation == 'HELLO':
            if origin not in self.neighbors:
                self.neighbors.append(origin)
                print(f"Adicionando vizinho na tabela: {origin}")
            else:
                print(f"Vizinho já está na tabela: {origin}")
            client_socket.sendall(b"HELLO_OK\n")
        elif operation == 'SEARCH':
            mode = parts[4]
            if mode == 'FL':
                self.stats['flooding']['count'] += 1
                self.process_search_message(parts, client_socket)
            elif mode == 'BP':
                self.stats['depth_search']['count'] += 1
                self.process_depth_search_message(parts, client_socket)
            elif mode == 'RW':
                self.stats['random_walk']['count'] += 1
                self.process_random_walk_message(parts, client_socket)
        elif operation == 'VAL':
            mode = parts[4]
            hop_count = int(parts[7])
            if mode == 'FL':
                self.stats['flooding']['hops'].append(hop_count)
            elif mode == 'BP':
                self.stats['depth_search']['hops'].append(hop_count)
            elif mode == 'RW':
                self.stats['random_walk']['hops'].append(hop_count)
            print(f"Valor encontrado! Chave: {parts[5]} valor: {parts[6]}")
        elif operation == 'BYE':
            print(f"Mensagem recebida: {message}")
            if origin in self.neighbors:
                self.neighbors.remove(origin)
                print(f"Removendo vizinho da tabela: {origin}")

    def process_search_message(self, parts, client_socket):
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        mode = parts[4]
        last_hop_port = int(parts[5])
        key = parts[6]
        hop_count = int(parts[7])

        msg_id = (origin, seq_no)
        if msg_id in self.seen_messages:
            print("Flooding: Mensagem repetida!")
            return

        self.seen_messages.add(msg_id)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.address}:{self.port} {self.sequence_number} {self.ttl_default} VAL {mode} {key} {value} {hop_count}\n"
            self.sequence_number += 1
            self.send_message(response, origin)
            print(f"Valor encontrado! Chave: {key} valor: {value}")
            return

        ttl -= 1
        if ttl == 0:
            print("TTL igual a zero, descartando mensagem")
            return

        hop_count += 1
        new_message = f"{origin} {seq_no} {ttl} SEARCH {mode} {self.port} {key} {hop_count}\n"
        for neighbor in self.neighbors:
            if neighbor.split(':')[1] != str(last_hop_port):
                self.send_message(new_message, neighbor)

    def process_depth_search_message(self, parts, client_socket):
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        last_hop_port = int(parts[5])
        key = parts[6]
        hop_count = int(parts[7])
        msg_id = (origin, seq_no)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.address}:{self.port} {self.sequence_number} {self.ttl_default} VAL BP {key} {value} {hop_count}\n"
            self.sequence_number += 1
            self.send_message(response, origin)
            print(f"Valor encontrado! Chave: {key} valor: {value}")
            return

        ttl -= 1
        if ttl == 0:
            print("TTL igual a zero, descartando mensagem")
            return

        if msg_id not in self.depth_search_info:
            self.depth_search_info[msg_id] = {
                'noh_mae': f"{self.address}:{self.port}",
                'vizinhos_candidatos': self.neighbors[:],
                'vizinho_ativo': None
            }
        
        info = self.depth_search_info[msg_id]

        if f"{self.address}:{last_hop_port}" in info['vizinhos_candidatos']:
            info['vizinhos_candidatos'].remove(f"{self.address}:{last_hop_port}")

        if info['noh_mae'] == f"{self.address}:{self.port}" and info['vizinho_ativo'] == f"{self.address}:{last_hop_port}" and not info['vizinhos_candidatos']:
            print(f"BP: Não foi possível localizar a chave {key}")
            return

        if info['vizinho_ativo'] and info['vizinho_ativo'] != f"{self.address}:{last_hop_port}":
            print("BP: Ciclo detectado, devolvendo a mensagem...")
            self.send_message(f"{origin} {seq_no} {ttl} SEARCH BP {self.port} {key} {hop_count + 1}\n", f"{self.address}:{last_hop_port}")
            return

        if not info['vizinhos_candidatos']:
            print("BP: Nenhum vizinho encontrou a chave, retrocedendo...")
            self.send_message(f"{origin} {seq_no} {ttl} SEARCH BP {self.port} {key} {hop_count + 1}\n", info['noh_mae'])
            return

        next_neighbor = random.choice(info['vizinhos_candidatos'])
        info['vizinho_ativo'] = next_neighbor
        info['vizinhos_candidatos'].remove(next_neighbor)

        new_message = f"{origin} {seq_no} {ttl} SEARCH BP {self.port} {key} {hop_count + 1}\n"
        self.send_message(new_message, next_neighbor)

    def process_random_walk_message(self, parts, client_socket):
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        last_hop_port = int(parts[5])
        key = parts[6]
        hop_count = int(parts[7])
        msg_id = (origin, seq_no)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.address}:{self.port} {self.sequence_number} {self.ttl_default} VAL RW {key} {value} {hop_count}\n"
            self.sequence_number += 1
            self.send_message(response, origin)
            print(f"Valor encontrado! Chave: {key} valor: {value}")
            return

        ttl -= 1
        if ttl == 0:
            print("TTL igual a zero, descartando mensagem")
            return

        hop_count += 1
        new_message = f"{origin} {seq_no} {ttl} SEARCH RW {self.port} {key} {hop_count}\n"
        neighbors_to_choose = [neighbor for neighbor in self.neighbors if int(neighbor.split(':')[1]) != last_hop_port]

        if neighbors_to_choose:
            next_neighbor = random.choice(neighbors_to_choose)
        else:
            next_neighbor = f"{self.address}:{last_hop_port}"

        self.send_message(new_message, next_neighbor)

    def send_hello(self, neighbor):
        try:
            neighbor_address, neighbor_port = neighbor.split(':')
            neighbor_port = int(neighbor_port)
            with socket.create_connection((neighbor_address, neighbor_port)) as sock:
                message = f"{self.address}:{self.port} {self.sequence_number} 1 HELLO\n"
                self.sequence_number += 1
                print(f"Encaminhando mensagem {message.strip()} para {neighbor}")
                sock.sendall(message.encode())
                response = sock.recv(1024).decode().strip()
                if response == "HELLO_OK":
                    print(f"Envio feito com sucesso: {message.strip()}")
                    return True
                else:
                    print(f"Erro ao enviar mensagem: {message.strip()}")
                    return False
        except Exception as e:
            print(f"Erro ao conectar-se ao vizinho {neighbor}: {e}")
            return False

    def send_message(self, message, neighbor):
        try:
            neighbor_address, neighbor_port = neighbor.split(':')
            with socket.create_connection((neighbor_address, int(neighbor_port))) as sock:
                print(f"Encaminhando mensagem {message.strip()} para {neighbor}")
                sock.sendall(message.encode())
                print(f"Envio feito com sucesso: {message.strip()}")
        except Exception as e:
            print(f"Erro ao enviar mensagem para {neighbor}: {e}")

    def show_menu(self):
        while True:
            print("Escolha o comando")
            print("[0] Listar vizinhos")
            print("[1] HELLO")
            print("[2] SEARCH (flooding)")
            print("[3] SEARCH (random walk)")
            print("[4] SEARCH (busca em profundidade)")
            print("[5] Estatisticas")
            print("[6] Alterar valor padrao de TTL")
            print("[9] Sair")
            choice = input()
            if choice == '0':
                self.list_neighbors()
            elif choice == '1':
                print("Escolha o vizinho:")
                self.list_neighbors()
                neighbor_choice = int(input())
                neighbor = self.neighbors[neighbor_choice]
                self.send_hello(neighbor)
            elif choice == '2':
                self.initiate_search('FL')
            elif choice == '3':
                self.initiate_search('RW')
            elif choice == '4':
                self.initiate_search('BP')
            elif choice == '5':
                self.show_statistics()
            elif choice == '6':
                self.change_default_ttl()
            elif choice == '9':
                self.exit_network()
                break

    def list_neighbors(self):
        print("Lista de vizinhos:")
        for count, neighbor in enumerate(self.neighbors):
            print(f"[{count}] {neighbor}")

    def send_hello_to_all(self):
        for neighbor in self.neighbors:
            self.send_hello(neighbor)

    def initiate_search(self, mode):
        key = input("Digite a chave a ser buscada\n")
        message = f"{self.address}:{self.port} {self.sequence_number} {self.ttl_default} SEARCH {mode} {self.port} {key} 0\n"
        self.sequence_number += 1
        if mode == 'RW':
            neighbor = random.choice(self.neighbors)
            self.send_message(message, neighbor)
        else:
            for neighbor in self.neighbors:
                self.send_message(message, neighbor)

    def show_statistics(self):
        print("Estatisticas")
        print(f"Total de mensagens de flooding vistas: {self.stats['flooding']['count']}")
        print(f"Total de mensagens de random walk vistas: {self.stats['random_walk']['count']}")
        print(f"Total de mensagens de busca em profundidade vistas: {self.stats['depth_search']['count']}")

        if self.stats['flooding']['hops']:
            flooding_mean = statistics.mean(self.stats['flooding']['hops'])
            flooding_stdev = statistics.stdev(self.stats['flooding']['hops']) if len(self.stats['flooding']['hops']) > 1 else 0
        else:
            flooding_mean = flooding_stdev = 0
        print(f"Media de saltos ate encontrar destino por flooding: {flooding_mean}")
        print(f"Desvio padrão de saltos ate encontrar destino por flooding: {flooding_stdev}")

        if self.stats['random_walk']['hops']:
            random_walk_mean = statistics.mean(self.stats['random_walk']['hops'])
            random_walk_stdev = statistics.stdev(self.stats['random_walk']['hops']) if len(self.stats['random_walk']['hops']) > 1 else 0
        else:
            random_walk_mean = random_walk_stdev = 0
        print(f"Media de saltos ate encontrar destino por random walk: {random_walk_mean}")
        print(f"Desvio padrão de saltos ate encontrar destino por random walk: {random_walk_stdev}")

        if self.stats['depth_search']['hops']:
            depth_search_mean = statistics.mean(self.stats['depth_search']['hops'])
            depth_search_stdev = statistics.stdev(self.stats['depth_search']['hops']) if len(self.stats['depth_search']['hops']) > 1 else 0
        else:
            depth_search_mean = depth_search_stdev = 0
        print(f"Media de saltos ate encontrar destino por busca em profundidade: {depth_search_mean}")
        print(f"Desvio padrão de saltos ate encontrar destino por busca em profundidade: {depth_search_stdev}")

    def change_default_ttl(self):
        new_ttl = int(input("Digite novo valor de TTL\n"))
        self.ttl_default = new_ttl

    def exit_network(self):
        print("Saindo...")
        for neighbor in self.neighbors:
            message = f"{self.address}:{self.port} {self.sequence_number} 1 BYE\n"
            self.sequence_number += 1
            self.send_message(message, neighbor)
        self.server_socket.close()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 peer_node.py <IP> <PORT> [<NEIGHBORS_FILE>] [<KEY_VALUE_FILE>]")
        sys.exit(1)

    address = sys.argv[1]
    port = sys.argv[2]
    neighbors_file = sys.argv[3] if len(sys.argv) > 3 else None
    key_value_file = sys.argv[4] if len(sys.argv) > 4 else None

    PeerNode(address, port, neighbors_file, key_value_file)