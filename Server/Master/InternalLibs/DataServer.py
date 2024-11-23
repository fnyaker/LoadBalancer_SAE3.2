import time
import json
from threading import Thread
from Server.Master.InternalLibs.Server import Server
from cryptography.fernet import Fernet

class Session :
    """This class correspond to a user that
     is connected to the data server for
     compiling and running code in the cloud.
      The user stays the same but the node can change"""
    def __init__(self, UserObject):
        self.__clientObject = UserObject
        self.__node = None

    def useNode(self, node):
        self.__node = node


    def relay(self):
        data = self.__clientObject.get_last_message()
        if data:
            if self.__node:
                self.__node.send(data)




class Listener(Server): # this class listens
    """The User must auth itself by sending his UID encrypted with the key given to him by the server"""
    def __init__(self, listen_ip, listen_port, callback):
        self.__listen_ip = listen_ip
        self.__listen_port = listen_port
        self.__running = True
        self.__authorised_client = [] # (uid, key)
        self.__callback = callback

        super().__init__(self.__listen_port, self.__listen_ip, self.__authenticate)

    def __authenticate(self, clientObject):
        time.sleep(0.1)
        print("Authenticating client")
        auth_pass = False
        remaining = 3
        print("Authorised clients:", self.__authorised_client)
        while not auth_pass and remaining > 0:
            print("Remaining tries:", remaining)
            data = clientObject.get_last_message()
            if data:
                for i in self.__authorised_client:
                    try :
                        decrypted = self.__decrypt(data, i[1])
                        print("Decrypted:", decrypted)
                        if decrypted == i[0]:
                            clientObject.send(self.__encrypt(json.dumps({"command" : "Auth_pass"}), i[1]))
                            auth_pass = True
                            break
                    except:
                        pass

            remaining -= 1

        if auth_pass:
            print("Client authorised")

            self.__callback(clientObject)
        else:
            print("Client denied")
            clientObject.close()

    def start(self):
        super().start()
        print("Listener started")

    def add_authorised_client(self, uid, key):
        print("Adding authorised client")
        self.__authorised_client.append((uid, key))


    def __decrypt(self, data, key:str):
        cypher = Fernet(key.encode('utf-8'))

        return cypher.decrypt(data).decode('utf-8')

    def __encrypt(self, data, key:str):
        cypher = Fernet(key.encode('utf-8'))
        return cypher.encrypt(data.encode('utf-8'))

class DataServer:
    """The base class for other server classes"""

    def __init__(self, userlisten_ip, userlisten_port, node_listen_ip, node_listen_port, pipe):
        self.__userListener = Listener(userlisten_ip, userlisten_port, self.__new_user)
        self.__nodeListener = Listener(node_listen_ip, node_listen_port, self.__new_node)
        self.__pipe = pipe
        self.__mainThread = Thread(target=self.__main)
        self.__nodes = [ # here there will be waiting nodes to be used (NodeObject, AssignedUserUid)

        ]
        self.__sessions = [

            ]
        self.__running = True


    def start(self):
        self.__userListener.start()
        self.__nodeListener.start()
        self.__mainThread.start()
        print("Data server started")


    def __new_user(self, clientObject):
        self.__sessions.append(Session(clientObject))

    def __new_node(self, clientObject):
        pass

    def __main(self):
        while self.__running:
            self.__checkformsg()
            time.sleep(0.01)

    def __checkformsg(self):
        if self.__pipe.poll_from_server():
            msg = self.__pipe.recv_from_server()
            if msg:
                self.__handle_messages(msg)


    def __handle_messages(self,msg):
        obj = json.loads(msg)
        if "command" in obj:
            if obj["command"] == "DataSessionRequest":
                self.__userListener.add_authorised_client(obj["uid"], obj["Key"])
