import socket
import ssl
import json
from threading import Thread
import time
from cryptography.fernet import Fernet

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
            self.__context.check_hostname = False
            self.__context.verify_mode = ssl.CERT_NONE
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
        print(data)
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
        elif obj['command'] == 'DataSession':
            print("Got node, i'm happy")
            print(obj['data'])
            # the client is happy to have a node
            # he will now connect a data client to the Master server (proxy) for fast data transfer
            self.initDataClient(obj['data']['ip'], obj['data']['port'], obj['data']['key'], self.__uid)



    def initDataClient(self, serverAddress, serverPort, encryptionKey = None, uid = None):
        self.__dataClient = DataClient(serverAddress, serverPort, encryptionKey, uid = uid)
        self.__dataClient.authenticate()
        self.__dataClient.startMsgListener()


    def requestUid(self):
        print("Requesting uid from server")
        self.__send(json.dumps({"command": "greet", "data": "Hello"}))

    def requestNode(self, RequiredPackages):
        self.__send(json.dumps({"command": "initDataSession", "RequiredPackages": RequiredPackages}))

    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}))

    @property
    def uid(self):
        return self.__uid



class DataClient(Client): # this is the client for the node connection, it must not use ssl as the data will be encrypted on the application layer
    def __init__(self, serverAddress = "localhost", serverPort = 22345, encryptionKey : str = None, payload = None, uid = None):
        super().__init__(serverAddress, serverPort, False) # no full ssl because master will serve as proxy and we d'ont want to overload it the data will be encrypted on the application layer
        self.__encryptionKey = encryptionKey
        self.__cypher = Fernet(encryptionKey.encode('utf-8'))
        self.running = True
        self.pingtime = None
        self.__uid = uid
        self.__payload = None
        self.__auth_passed = False

    def __listener(self):
        while self.running:
            try :
                data = self.__receive(2048)
            except :
                continue
            if data:
                self.__handleMessages(self.__decrypt(data).decode('utf-8'))
            else:
                pass


    def startMsgListener(self):
        self.__listenerThread = Thread(target=self.__listener)
        self.__listenerThread.start()
        print("DataClient started")

    def authenticate(self):
        print("Authenticating")
        self.__send(self.__uid.encode('utf-8'))



    def __handleMessages(self, data : str):
        print(data)
        obj = json.loads(data)
        if obj['command'] == 'Ready':
            self.sendPayload()
        elif obj['command'] == 'PONG':
            try :
                self.pingtime = time.time() - self.pingtime
                print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass
        elif obj['command'] == 'Status':
            self.updateStatus(obj['data'])
        elif obj['command'] == 'STDOUT':
            self.STDOUT(obj['data'])
        elif obj['command'] == 'STDERR':
            self.STDERR(obj['data'])
        elif obj['command'] == 'OUT':
            self.running = False
        elif obj['command'] == 'Auth_pass':
            print("Authenticated, woaw")
            self.__auth_passed = True


    def updateStatus(self, status : str):
        print(status)

    def STDOUT(self, data : str):
        print(data)

    def STDERR(self, data : str):
        print(data)

    def sendPayload(self, data : bytes):
        self.__send(self.__payload)

    def __encrypt(self, data : bytes):
        return self.__cypher.encrypt(data)

    def __decrypt(self, data : bytes):
        return self.__cypher.decrypt(data)


    def __send(self, data : bytes):
        if self.__encryptionKey:
            # encrypt data
            data = self.__encrypt(data)
        super().send(data)

    def __receive(self, size : 2048):
        data = super().receive(size)
        if self.__encryptionKey:
            # decrypt data
            pass
        return data

    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}).encode('utf-8'))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}).encode('utf-8'))





