import sys
from datetime import datetime
from peer_node import PeerNode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python3 peer_node.py <IP>:<PORT> [<NEIGHBORS_FILE>] [<KEY_VALUE_FILE>]"
        )
        sys.exit(1)

    address, port = sys.argv[1].split(":")
    neighbors_file = sys.argv[2] if len(sys.argv) > 2 else None
    key_value_file = sys.argv[3] if len(sys.argv) > 3 else None

    def log(message, prefix="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = prefix.upper()
        print(f"[{timestamp}] [{address}:{port}] [{prefix}]: {message}")

    PeerNode(address, port, neighbors_file, key_value_file, start_server=True)
