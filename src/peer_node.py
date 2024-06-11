import sys
from message import MessageHandler
from search_strategy import (
    SearchStrategyContext,
    FloodingSearchStrategy,
    RandomWalkSearchStrategy,
    DepthFirstSearchStrategy,
)
from server import PeerServer
from statistics import Statistics


class PeerNode:
    def __init__(
        self,
        address,
        port,
        neighbors_file=None,
        key_value_file=None,
        start_server=False,
    ):
        self.address = address
        self.port = int(port)
        self.neighbors = []
        self.key_value_store = {}
        self.sequence_number = 0
        self.ttl_default = 100
        self.seen_messages = set()
        self.depth_search_info = {}
        self.stats = Statistics()

        if neighbors_file:
            self.load_file(neighbors_file, self.add_neighbor)
        if key_value_file:
            self.load_file(key_value_file, self.add_key_value)

        self.server = PeerServer(self.address, self.port, self)
        self.message_handler = MessageHandler(self)
        self.search_context = SearchStrategyContext()

        if start_server:
            self.start_server()
            self.show_menu()

    def load_file(self, file_path, handler):
        with open(file_path, "r") as file:
            for line in file:
                handler(line.strip())

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)
        main.log(f"Tentando adicionar vizinho {neighbor}")
        self.message_handler.send_hello(neighbor)

    def add_key_value(self, key_value):
        key, value = key_value.split()
        self.key_value_store[key] = value

    def start_server(self):
        self.server.start()

    def show_menu(self):
        while True:
            choice = input(
                "Escolha o comando:\n"
                "[0] Listar vizinhos\n"
                "[1] HELLO\n"
                "[2] SEARCH (flooding)\n"
                "[3] SEARCH (random walk)\n"
                "[4] SEARCH (busca em profundidade)\n"
                "[5] Estatisticas\n"
                "[6] Alterar valor padrao de TTL\n"
                "[9] Sair\n"
            )
            if choice == "0":
                self.list_neighbors()
            elif choice == "1":
                neighbor_choice = input("Escolha o vizinho:\n")
                self.message_handler.send_hello(neighbor_choice)
            elif choice == "2":
                self.initiate_search(FloodingSearchStrategy(self))
            elif choice == "3":
                self.initiate_search(RandomWalkSearchStrategy(self))
            elif choice == "4":
                self.initiate_search(DepthFirstSearchStrategy(self))
            elif choice == "5":
                self.stats.show_statistics()
            elif choice == "6":
                self.ttl_default = int(input("Digite novo valor de TTL\n"))
            elif choice == "9":
                self.exit_network()
                break

    def list_neighbors(self):
        log("Lista de vizinhos:")
        for neighbor in self.neighbors:
            log(neighbor)

    def initiate_search(self, strategy):
        key = input("Digite a chave a ser buscada\n")
        self.search_context.set_strategy(strategy)
        self.search_context.search(key)

    def exit_network(self):
        log("Saindo...")
        for neighbor in self.neighbors:
            message = f"{self.address}:{self.port} {self.sequence_number} 1 BYE\n"
            self.sequence_number += 1
            self.message_handler.send_message(message, neighbor)
        self.server.close()
        if hasattr(sys, "_called_from_test"):
            return
        sys.exit(0)
