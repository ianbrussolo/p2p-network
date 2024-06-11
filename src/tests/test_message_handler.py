import unittest
from unittest.mock import patch, MagicMock
from message import MessageHandler
from peer_node import PeerNode


class TestMessageHandler(unittest.TestCase):
    def setUp(self):
        self.peer_node = PeerNode("127.0.0.1", 8000)
        self.message_handler = MessageHandler(self.peer_node)

    @patch("message.socket.create_connection")
    def test_send_message_success(self, mock_create_connection):
        # Mock the socket object
        mock_socket = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_socket
        neighbor = "127.0.0.1:8001"
        message = "127.0.0.1:8000 1 100 HELLO"

        # Define the return value for recv
        mock_socket.recv.return_value = b"HELLO_OK\n"

        self.message_handler.send_message(message, neighbor)

        # Check that the connection was made correctly
        mock_create_connection.assert_called_with(("127.0.0.1", 8001))
        # Check that the message was sent correctly
        mock_socket.sendall.assert_called_with(message.encode())
        # Check that recv was called once
        mock_socket.recv.assert_called_once_with(1024)
        # Ensure the response was processed correctly
        self.assertEqual(mock_socket.recv.return_value.decode().strip(), "HELLO_OK")

    @patch("message.socket.create_connection")
    def test_send_message_error(self, mock_create_connection):
        mock_create_connection.side_effect = Exception("Connection error")
        neighbor = "127.0.0.1:8001"
        message = "127.0.0.1:8000 1 100 HELLO"

        self.message_handler.send_message(message, neighbor)

        mock_create_connection.assert_called_with(("127.0.0.1", 8001))
        print("Erro ao conectar-se ao vizinho 127.0.0.1:8001: Connection error")


if __name__ == "__main__":
    unittest.main()
