import statistics


class Statistics:
    def __init__(self):
        self.stats = {
            "flooding": {"count": 0, "hops": []},
            "random_walk": {"count": 0, "hops": []},
            "depth_search": {"count": 0, "hops": []},
        }

    def increment_count(self, method):
        self.stats[method]["count"] += 1

    def record_hop(self, method, hop_count):
        self.stats[method]["hops"].append(hop_count)

    def show_statistics(self):
        print("Estatisticas")
        self.print_method_stats("flooding")
        self.print_method_stats("random_walk")
        self.print_method_stats("depth_search")

    def print_method_stats(self, method):
        count = self.stats[method]["count"]
        hops = self.stats[method]["hops"]
        if hops:
            mean = statistics.mean(hops)
            stdev = statistics.stdev(hops) if len(hops) > 1 else 0
        else:
            mean = stdev = 0
        print(f"Total de mensagens de {method} vistas: {count}")
        print(f"Media de saltos ate encontrar destino por {method}: {mean}")
        print(f"Desvio padrão de saltos ate encontrar destino por {method}: {stdev}")
