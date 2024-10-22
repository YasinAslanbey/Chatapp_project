import tkinter as tk
import socket
import threading
import logging
import logging.config

# Logging Configuration
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s %(name)s [%(process)d:%(thread)d] %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'client.log',
            'formatter': 'detailed',
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
})

class EpicChatApp:
    def __init__(self, root):
        self.root = root
        self.socket = None
        self.username = ""
        self.setup_login_ui()

    def setup_login_ui(self):
        self.root.title("Cyberpunk_telecomunicaton - Login")

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(padx=10, pady=10)

        self.username_label = tk.Label(self.login_frame, text="Enter your username:")
        self.username_label.pack(pady=5)

        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack(pady=5)

        self.ip_label = tk.Label(self.login_frame, text="Enter IP address:")
        self.ip_label.pack(pady=5)

        self.ip_entry = tk.Entry(self.login_frame)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5)

        self.port_label = tk.Label(self.login_frame, text="Enter Port number:")
        self.port_label.pack(pady=5)

        self.port_entry = tk.Entry(self.login_frame)
        self.port_entry.insert(0, "8888")
        self.port_entry.pack(pady=5)

        self.login_button = tk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.pack(pady=5)

    def setup_chat_ui(self):
        self.root.title(f"Cyberpunk_telecomunicaton - {self.username}")

        self.login_frame.pack_forget()

        self.message_list = tk.Text(self.root, height=25, width=70, bg='#FFD300')
        self.message_list.pack(side=tk.TOP, padx=3, pady=3)

        self.user_list = tk.Listbox(self.root, height=10)
        self.user_list.pack(side=tk.LEFT, fill=tk.X, padx=3, pady=3)

        self.message_entry = tk.Entry(self.root, width=30, bg='#333333', fg='white')
        self.message_entry.pack(side=tk.RIGHT, fill=tk.X, padx=6, pady=6)

        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=6, pady=6)

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def login(self):
        self.username = self.username_entry.get()
        host = self.ip_entry.get()
        port = int(self.port_entry.get())

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            self.socket.sendall(f"USERNAME:{self.username}".encode('utf-8'))
            self.setup_chat_ui()
            self.message_list.insert(tk.END, "Connected to server\n")
            logging.info(f"Connected to server at {host}:{port} as {self.username}")
        except Exception as e:
            self.message_list.insert(tk.END, f"Failed to connect to server: {e}\n")
            logging.error(f"Failed to connect to server: {e}")

    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if message.startswith("USERLIST:"):
                    self.update_user_list(message[len("USERLIST:"):])
                else:
                    self.message_list.insert(tk.END, message + '\n')
                    self.message_list.yview(tk.END)
                    logging.debug(f"Received message: {message}")
            except Exception as e:
                self.message_list.insert(tk.END, f"Error receiving message: {e}\n")
                logging.error(f"Error receiving message: {e}")
                break

    def update_user_list(self, users):
        self.user_list.delete(0, tk.END)
        for user in users.split(','):
            self.user_list.insert(tk.END, user)
        logging.debug(f"Updated user list: {users}")

    def send_message(self):
        message = self.message_entry.get()
        if message:
            try:
                self.socket.sendall(f"{self.username}: {message}".encode('utf-8'))
                self.message_list.insert(tk.END, f"Me: {message}\n")
                self.message_list.yview(tk.END)
                self.message_entry.delete(0, tk.END)
                logging.info(f"Sent message: {message}")
            except Exception as e:
                self.message_list.insert(tk.END, f"Error sending message: {e}\n")
                logging.error(f"Error sending message: {e}")

    def on_closing(self):
        try:
            self.socket.sendall(f"DISCONNECT:{self.username}".encode('utf-8'))
            self.socket.close()
            logging.info(f"{self.username} disconnected from server")
        except Exception as e:
            logging.error(f"Error closing socket: {e}")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    client = EpicChatApp(root)
    root.protocol("WM_DELETE_WINDOW", client.on_closing)
    root.mainloop()
