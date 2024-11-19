import socket
from threading import Thread

class CommServer:
    def __init__(self, host='localhost', port=12347):
        self.__host = host
        self.__port = port
        self.__clients = []
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(5)
        self.__running = True

    def start(self):
        print(f"CommServer starting on {self.__host}:{self.__port}")
        self.__accept_thread = Thread(target=self.__accept_clients)
        self.__accept_thread.start()

    def __accept_clients(self):
        while self.__running:
            client_socket, client_address = self.__server_socket.accept()
            self.__clients.append(client_socket)
            print(f"New client connected: {client_address}")
            Thread(target=self.__handle_client, args=(client_socket,)).start()

    def __handle_client(self, client_socket):
        while self.__running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    print(f"Received message: {message}")
                    self.__broadcast(message, client_socket)
            except ConnectionResetError:
                break
        client_socket.close()

    def __broadcast(self, message, sender_socket):
        for client_socket in self.__clients:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except BrokenPipeError:
                    self.__clients.remove(client_socket)

    def stop(self):
        self.__running = False
        self.__server_socket.close()
        self.__accept_thread.join()
        print("CommServer stopped")