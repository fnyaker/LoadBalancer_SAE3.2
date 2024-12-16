# import sys
# import os

# from click import command

# Ajouter le répertoire parent au sys.path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
        self.sock = None

        if self.__useSSL:
            self.__context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.__certfile)
            self.__context.check_hostname = False
            self.__context.verify_mode = ssl.CERT_NONE
            self.sock = self.__context.wrap_socket(socket.create_connection((self.__serverAddress, self.__serverPort)), server_hostname=self.__serverAddress)
        else:
            self.sock = socket.create_connection((self.__serverAddress, self.__serverPort))


    def send(self, data : bytes):
        if self.__useSSL:
            self.sock.sendall(data)
        else:
            self.sock.send(data)

    def receive(self, size : 2048):
        return self.sock.recv(size)

    def close(self):
        self.sock.close()

    @property
    def addr(self):
        return self.sock.getpeername()

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
        self.__code = None
        self.printbuffer = [] # this is a buffer for the gui to print the output of the backend
        self.__dataClient = None
        self.__dataclientRunning = False

    def print(self,msg):
        self.printbuffer.append(msg)


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
            print("usefull")
            #if self.__dataClient:
            #    if not self.__dataClient.running:
            #        self.print("Client de données se ferme")
            #        self.__dataClient.end()
            #        self.__dataClient = None
            #        self.print("Client de données fermé (normalement)")

    def startListener(self):
        self.__listenerThread = Thread(target=self.__listener)
        self.__listenerThread.start()

    def __handleMessages(self, data : str):
        print(data)
        obj = json.loads(data)
        if obj['command'] == 'uidIs':
            self.__uid = obj['uid']
        elif obj['command'] == 'OUT':
            self.print("DECONNEXION DEMANDEE PAR LE SERVEUR")
            self.closedataclient()
            self.selfkill()
            self.print("DECONNECTÉ")

        elif obj['command'] == 'pong':
            try :
                self.pingtime = time.time() - self.pingtime
                # print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass
        elif obj['command'] == 'ping':
            # print("I live !")
            self.__send(json.dumps({"command": "pong"}))

        elif obj['command'] == 'DataSession':
            # print("Got node, i'm happy")
            # print(obj['data'])
            self.print("Le serveur m'a attribué un noeud")
            # the client is happy to have a node
            # he will now connect a data client to the Master server (proxy) for fast data transfer
            self.initDataClient(obj['data']['ip'], obj['data']['port'], obj['data']['key'], self.__uid)
        elif obj['command'] == 'EndDataSession':
            self.print("Le serveur a mis fin à la session de données")
            self.closedataclient()



    def initDataClient(self, serverAddress, serverPort, encryptionKey = None, uid = None):
        self.__dataclientRunning = True
        self.__dataClient = DataClient(serverAddress, serverPort, encryptionKey, uid = uid, payload = self.__code, print_callback = self.print)
        self.__dataClient.authenticate()
        self.__dataClient.startMsgListener()

    def closedataclient(self):
        if self.__dataclientRunning:
            self.__dataclientRunning = False
            self.print("Client de données se ferme")
            try :
                self.__dataClient.running = False
                print(1)
                self.__dataClient.end()
                print(2)
            except:
                pass

            time.sleep(0.5)
            self.__dataClient = None
            self.print("Client de données Fermé")



    def requestUid(self):
        print("Requesting uid from server")
        self.__send(json.dumps({"command": "greet", "data": "Hello"}))

    def requestNode(self, RequiredPackages):
        self.__send(json.dumps({"command": "initDataSession", "RequiredPackages": RequiredPackages}))

    def runCode(self, code : str):
        self.__code = code
        self.requestNode(self.detect_language(code))

    def detect_language(self, code):
        """
        Detecte le langage de programmation d'un fichier en analysant son contenu.

        Args:
            code (str): Code source à analyser.

        Returns:
            str: Le langage de programmation détecté ('c', 'cpp', 'java', 'python', 'inconnu').
        """
        content = code

        # Recherche de mots-clés pour chaque langage
        if '#include' in content and 'stdio.h' in content:
            return 'c'
        elif '#include' in content and 'iostream' in content:
            return 'cpp'
        elif 'public class' in content:
            return 'java'
        elif 'print(' in content or 'def' in content:
            return 'python'
        else:
            return 'inconnu'

    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}))

    def selfkill(self):
        try :
            self.__send(json.dumps({"command": "OUT"}))
        except:
            pass
        self.running = False
        super().close()

    @property
    def uid(self):
        return self.__uid

    @property
    def dataclient_running(self):
        return True if self.__dataClient else False





class DataClient(Client): # this is the client for the node connection, it must not use ssl as the data will be encrypted on the application layer
    def __init__(self, serverAddress = "server", serverPort = 22345, encryptionKey : str = None, payload = None, uid = None, print_callback = None, kill_callback = None):
        super().__init__(serverAddress, serverPort, False) # no full ssl because master will serve as proxy and we d'ont want to overload it the data will be encrypted on the application layer
        self.__encryptionKey = encryptionKey
        # print("Key:", encryptionKey)
        self.__cypher = Fernet(encryptionKey.encode('utf-8'))
        self.running = True
        self.pingtime = None
        self.__uid = uid
        self.__payload = payload
        self.__auth_passed = False
        if print_callback:
            self.print = print_callback
        else:
            self.print = print

        if kill_callback:
            self.kill = kill_callback
        else:
            self.kill = self.close

        self.print("Initialisation du client de données")
        self.print("Le code est : " + payload)

    def __listener(self):
        while self.running:
            try :
                # print("Listening for data")
                data = self.__receive(4096)
                # if the connection was closed, we will get an empty data
            except :
                continue
            if data:
                #print("Got data")
                self.__handleMessages(self.__decrypt(data).decode('utf-8'))
                #print("Handled data")
            else:
                self.running = False

        # auto close the connection
        print("Closing connection")
        #self.kill()


    def end(self):
        self.close()
        print("joining thread")
        del super().sock
        del self.__listenerThread
        del self.__cypher
        del self.__encryptionKey
        del self.__uid
        del self.__payload
        del self.__auth_passed
        del self

        # self.__listenerThread.join()



    def startMsgListener(self):
        self.__listenerThread = Thread(target=self.__listener)
        self.__listenerThread.start()
        self.print("Client de données initialisé")

    def authenticate(self):
        self.print("Authentification en cours du client de données")
        self.__send(self.__uid.encode('utf-8'))


    def __handleMessages(self, data : str):
        # print(data)
        try :
            obj = json.loads(data)
        except json.JSONDecodeError:
            self.print("Erreur de décodage des données du noeud")
            return
        if obj['command'] == 'STDOUT':
            self.STDOUT(obj['data'])
        elif obj['command'] == 'STDERR':
            self.STDERR(obj['data'])
        elif obj['command'] == 'Ready':
            if obj['data'] == self.__uid:
                self.print("Node ready for me !")
            self.sendPayload()

        elif obj['command'] == 'ping':
            print("I live !")
            self.__send(json.dumps({"command": "pong"}).encode('utf-8'))

        elif obj['command'] == 'pong':
            try :
                self.pingtime = time.time() - self.pingtime
                print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass
        elif obj['command'] == 'Status':
            self.updateStatus(obj['data'])

        elif obj['command'] == 'OUT':
            print("Node sent OUT command")
            self.running = False
        elif obj['command'] == 'Auth_pass':
            print("Authenticated, woaw")
            self.__auth_passed = True
        elif obj['command'] == 'PayloadExecuted':
            self.print("Payload executed")
            #self.sayBye()
            #self.close()
            self.running = False


    def updateStatus(self, status : str):
        # this one should be printed in the color 2 (green)
        self.print(("\033[92m" + "Node Status: " +  status + "\033[0m"))

    def STDOUT(self, data : str):
        self.print(data)

    def STDERR(self, data : str):
        # we want to print it in red color
        self.print("\033[91m" + data + "\033[0m")


    def sendPayload(self):
        self.print("Sending payload to node : " + self.__payload)
        self.__send(json.dumps({"command": "Payload", "data": self.__payload}).encode('utf-8'))

    def __encrypt(self, data : bytes):
        return self.__cypher.encrypt(data)

    def __decrypt(self, data : bytes):
        try:
            return self.__cypher.decrypt(data)
        except:
            return b''


    def __send(self, data : bytes):
        if self.__encryptionKey:
            # encrypt data
            data = self.__encrypt(data)
        super().send(data)

    #def __receive(self, buffer_size=1024):
    #    data = b''
    #    while True:
    #        part = super().receive(buffer_size)
    #        data += part
    #        if len(part) < buffer_size:
    #            break
    #    return data

    def __receive(self, buffer_size=4096):
        data = b''
        while True:
            part = super().receive(buffer_size)
            if not part:
                break
            data += part
            if len(part) < buffer_size:
                break
        return data

    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}).encode('utf-8'))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}).encode('utf-8'))





