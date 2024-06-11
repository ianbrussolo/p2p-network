import unittest
from unittest.mock import patch, MagicMock
from peer_node import PeerNode


class TestPeerNode(unittest.TestCase):
    def setUp(self):
        self.peer_node = PeerNode("127.0.0.1", 8000)

    @patch("message.MessageHandler.send_message")
    def test_add_neighbor(self, mock_send_message):
        neighbor = "127.0.0.1:8001"
        self.peer_node.add_neighbor(neighbor)

        self.assertIn(neighbor, self.peer_node.neighbors)
        mock_send_message.assert_called_with("127.0.0.1:8000 0 1 HELLO\n", neighbor)

    @patch("server.PeerServer.close")
    @patch("message.MessageHandler.send_message")
    def test_exit_network(self, mock_send_message, mock_close):
        neighbor = "127.0.0.1:8001"
        self.peer_node.neighbors.append(neighbor)
        self.peer_node.sequence_number = 5

        with patch("sys.exit") as mock_exit:
            self.peer_node.exit_network()

            mock_send_message.assert_called_with("127.0.0.1:8000 5 1 BYE\n", neighbor)
            mock_close.assert_called_once()
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
