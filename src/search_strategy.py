import random


class SearchStrategy:
    def __init__(self, peer_node):
        self.peer_node = peer_node

    def search(self, key, parts=None, client_socket=None):
        pass


class FloodingSearchStrategy(SearchStrategy):
    def search(self, key, parts=None, client_socket=None):
        origin, seq_no, ttl, last_hop_port, hop_count = self.parse_message(parts)
        if self.message_seen(origin, seq_no):
            return
        if self.key_found(key, origin, hop_count):
            return

        ttl -= 1
        if ttl == 0:
            return

        hop_count += 1
        new_message = self.create_message(origin, seq_no, ttl, key, hop_count, "FL")
        self.forward_message(new_message, last_hop_port)


class DepthFirstSearchStrategy(SearchStrategy):
    def search(self, key, parts=None, client_socket=None):
        origin, seq_no, ttl, last_hop_port, hop_count = self.parse_message(parts)
        if self.key_found(key, origin, hop_count):
            return

        ttl -= 1
        if ttl == 0:
            return

        msg_id = (origin, seq_no)
        if msg_id not in self.peer_node.depth_search_info:
            self.init_depth_info(msg_id)
        info = self.peer_node.depth_search_info[msg_id]

        if not info["vizinhos_candidatos"]:
            self.backtrack_message(
                origin, seq_no, ttl, key, hop_count, info, last_hop_port
            )
            return

        next_neighbor = random.choice(info["vizinhos_candidatos"])
        info["vizinho_ativo"] = next_neighbor
        info["vizinhos_candidatos"].remove(next_neighbor)

        new_message = self.create_message(origin, seq_no, ttl, key, hop_count + 1, "BP")
        self.peer_node.message_handler.send_message(new_message, next_neighbor)


class RandomWalkSearchStrategy(SearchStrategy):
    def search(self, key, parts=None, client_socket=None):
        pass


class SearchStrategyContext:
    def __init__(self):
        self.strategy = None

    def set_strategy(self, strategy):
        self.strategy = strategy

    def search(self, key, parts=None, client_socket=None):
        if self.strategy:
            self.strategy.search(key, parts, client_socket)


class BaseSearchStrategy(SearchStrategy):
    def parse_message(self, parts):
        origin = parts[0]
        seq_no = int(parts[1])
        ttl = int(parts[2])
        last_hop_port = int(parts[5])
        hop_count = int(parts[7])
        return origin, seq_no, ttl, last_hop_port, hop_count

    def message_seen(self, origin, seq_no):
        msg_id = (origin, seq_no)
        if msg_id in self.peer_node.seen_messages:
            print(f"Mensagem {msg_id} já vista, descartando")
            return True
        self.peer_node.seen_messages.add(msg_id)
        return False

    def key_found(self, key, origin, hop_count):
        if key in self.peer_node.key_value_store:
            value = self.peer_node.key_value_store[key]
            response = f"{self.peer_node.address}:{self.peer_node.port} {self.peer_node.sequence_number} {self.peer_node.ttl_default} VAL BP {key} {value} {hop_count}\n"
            self.peer_node.sequence_number += 1
            self.peer_node.message_handler.send_message(response, origin)
            print(f"Valor encontrado! Chave: {key} valor: {value}")
            return True
        return False

    def create_message(self, origin, seq_no, ttl, key, hop_count, method):
        return f"{origin} {seq_no} {ttl} SEARCH {method} {self.peer_node.port} {key} {hop_count}\n"

    def forward_message(self, new_message, last_hop_port):
        for neighbor in self.peer_node.neighbors:
            if neighbor.split(":")[1] != str(last_hop_port):
                self.peer_node.message_handler.send_message(new_message, neighbor)

    def init_depth_info(self, msg_id):
        self.peer_node.depth_search_info[msg_id] = {
            "noh_mae": f"{self.peer_node.address}:{self.peer_node.port}",
            "vizinhos_candidatos": self.peer_node.neighbors[:],
            "vizinho_ativo": None,
        }

    def backtrack_message(
        self, origin, seq_no, ttl, key, hop_count, info, last_hop_port
    ):
        if (
            info["vizinho_ativo"]
            and info["vizinho_ativo"] != f"{self.peer_node.address}:{last_hop_port}"
        ):
            print("BP: Ciclo detectado, devolvendo a mensagem...")
            self.peer_node.message_handler.send_message(
                f"{origin} {seq_no} {ttl} SEARCH BP {self.peer_node.port} {key} {hop_count + 1}\n",
                f"{self.peer_node.address}:{last_hop_port}",
            )
            return
        if not info["vizinhos_candidatos"]:
            print("BP: Nenhum vizinho encontrou a chave, retrocedendo...")
            self.peer_node.message_handler.send_message(
                f"{origin} {seq_no} {ttl} SEARCH BP {self.peer_node.port} {key} {hop_count + 1}\n",
                info["noh_mae"],
            )
