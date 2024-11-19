import socket
import ssl
import json
from threading import Thread
import time

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

class ControlClient(Client): # this is the client for the control connection, it must use ssl
    def __init__(self, serverAddress = "localhost", serverPort = 12345, certfile = None):
        super().__init__(serverAddress, serverPort, True, certfile)
        self.running = True
        self.__uid = None
        self.startListener()
        self.pingtime = None

    def __send (self, data : str):
        super().send(data.encode('utf-8'))

    def __listener(self):
        while self.running:
            try :
                data = self.receive(2048)
            except ssl.SSLWantReadError:
                continue
            if data:
                self.__handleMessages(data.decode('utf-8'))
            else:
                pass

    def startListener(self):
        self.__listenerThread = Thread(target=self.__listener)
        self.__listenerThread.start()

    def __handleMessages(self, data : str):
        print("Got message from server")
        obj = json.loads(data)
        if obj['command'] == 'uidIs':
            self.__uid = obj['uid']
        elif obj['command'] == 'OUT':
            self.running = False
        elif obj['command'] == 'pong':
            try :
                self.pingtime = time.time() - self.pingtime
                print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass


    def requestUid(self):
        print("Requesting uid from server")
        self.__send(json.dumps({"command": "greet", "data": "Hello"}))

    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}))

    @property
    def uid(self):
        return self.__uid



class DataClient(Client): # this is the client for the node connection, it must not use ssl as the data will be encrypted on the application layer
    def __init__(self, serverAddress = "localhost", serverPort = 12345):
        super().__init__(serverAddress, serverPort, False)


