import ssl
import socket


class Client:
    def __init__(self, serverAddress = "localhost", serverPort = 12345, useSSL = False, certfile = None):
        self.__serverAddress = serverAddress
        self.__serverPort = serverPort

        self.__useSSL = useSSL
        self.__certfile = certfile

        self.__context = None
        self.__sock = None

        if self.__useSSL:
            self.__context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.__certfile)
            self.__sock = self.__context.wrap_socket(socket.create_connection((self.__serverAddress, self.__serverPort)), server_hostname=self.__serverAddress)
        else:
            self.__sock = socket.create_connection((self.__serverAddress, self.__serverPort))


    def send(self, data : bytes):
        if self.__useSSL:
            self.__sock.sendall(data)
        else:
            self.__sock.send(data)

    def receive(self, size : 2048):
        return self.__sock.recv(size)

    def close(self):
        self.__sock.close()

    @property
    def addr(self):
        return self.__sock.getpeername()

    @property
    def useSSL(self):
        return self.__useSSL