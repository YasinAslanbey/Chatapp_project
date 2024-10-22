import unittest
from unittest.mock import patch, MagicMock
import socket
import threading

# Import the functions from the server code
from server import ChatServer, clients, usernames

class TestChatServer(unittest.TestCase):

    @patch('server.ChatServer.broadcast_user_list')
    def test_handle_client_username(self, mock_broadcast_user_list):
        server = ChatServer('127.0.0.1', 8888)
        mock_socket = MagicMock()
        mock_socket.recv.return_value = "USERNAME:testuser".encode('utf-8')
        
        with patch('server.clients', clients), patch('server.usernames', usernames):
            server.handle_client(mock_socket, ('127.0.0.1', 8888))

        self.assertIn(mock_socket, clients)
        self.assertEqual(clients[mock_socket], 'testuser')
        self.assertIn(mock_socket, usernames)
        self.assertEqual(usernames[mock_socket], 'testuser')
        mock_broadcast_user_list.assert_called_once()

    @patch('server.ChatServer.broadcast_user_list')
    def test_handle_client_disconnect(self, mock_broadcast_user_list):
        server = ChatServer('127.0.0.1', 8888)
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [
            "USERNAME:testuser".encode('utf-8'),
            "DISCONNECT:testuser".encode('utf-8')
        ]
        clients[mock_socket] = 'testuser'
        usernames[mock_socket] = 'testuser'

        with patch('server.clients', clients), patch('server.usernames', usernames):
            server.handle_client(mock_socket, ('127.0.0.1', 8888))

        self.assertNotIn(mock_socket, clients)
        self.assertNotIn(mock_socket, usernames)
        mock_broadcast_user_list.assert_called()

    @patch('server.clients', new_callable=dict)
    @patch('server.usernames', new_callable=dict)
    def test_broadcast(self, mock_clients, mock_usernames):
        server = ChatServer('127.0.0.1', 8888)
        mock_clients.update({
            'client1': MagicMock(),
            'client2': MagicMock()
        })
        message = "Hello, world!"
        
        server.broadcast(message, 'client1')
        
        mock_clients['client2'].sendall.assert_called_once_with(message.encode('utf-8'))

    @patch('server.clients', new_callable=dict)
    @patch('server.usernames', new_callable=dict)
    def test_broadcast_user_list(self, mock_clients, mock_usernames):
        server = ChatServer('127.0.0.1', 8888)
        mock_clients.update({
            'client1': MagicMock(),
            'client2': MagicMock()
        })
        mock_usernames.update({
            'client1': 'user1',
            'client2': 'user2'
        })
        
        server.broadcast_user_list()
        
        user_list_message = "USERLIST:user1,user2"
        for client in mock_clients.values():
            client.sendall.assert_called_with(user_list_message.encode('utf-8'))

    @patch('socket.socket')
    @patch('threading.Thread')
    def test_main(self, mock_thread, mock_socket):
        server = ChatServer('127.0.0.1', 8888)
        server.stop_event.clear()
        mock_server_socket = MagicMock()
        mock_socket.return_value = mock_server_socket
        mock_server_socket.accept.return_value = (MagicMock(), ('127.0.0.1', 8888))
        
        def stop_server_after_one_iteration(*args, **kwargs):
            server.stop_event.set()  # Stop the server loop after one iteration
        
        mock_thread.side_effect = stop_server_after_one_iteration
        
        with self.assertRaises(KeyboardInterrupt):
            server.start_server()
        
        mock_server_socket.bind.assert_called_with(('127.0.0.1', 8888))
        mock_server_socket.listen.assert_called_once()
        mock_thread.assert_called_once()

if __name__ == "__main__":
    unittest.main()
