from InternalLibs.Users.Users import *
from InternalLibs.Nodes.Nodes import *
from InternalLibs.Server import *
import uuid
from time import sleep
import os

from multiprocessing import Process

class NodeControlServer(Server): # this class is the one that listen for new nodes
    """The server class that listens for new nodes.
    It will manage them and allow them to connect to the master server and exchange the encryption key to connect to the user"""

    def __init__(self, listener_port, listener_ip, certfile, keyfile):
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl= True, certfile= certfile, keyfile= keyfile)
        self.nodesBook = NodesBook()

    def __genNodeUid(self):
        return str(uuid.uuid4())

    def __callback(self, ssl_client):
        print("New node connected")
        node_uid = self.__genNodeUid()
        node = Node(node_uid, ssl_client)
        self.nodesBook.addNode(node)

    def start(self):
        print("Node control server starting on", self.__listener_ip, ":", self.__listener_port)
        super().start()

class UserControlServer(Server): # this class is the one that listen for new users
    """The server class that listens for new users.
    It will manage them and allow them to get the key to connect to the node, it must be encrypted
    A second UserServer will be created for the master serve to serve as a relay between the user and the node"""
    def __init__(self, listener_port, listener_ip, certfile, keyfile):
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl= True, certfile= certfile, keyfile= keyfile)
        self.__userBook = UserBook()

    def start(self):
        print("User control server starting on", self.__listener_ip, ":", self.__listener_port)
        super().start()

    def __genClientUid(self):
        return str(uuid.uuid4())

    def __callback(self, ClientObject):
        client_uid = self.__genClientUid()
        client = User(client_uid, ClientObject)
        print("New user connected with uid", client_uid)
        self.__userBook.addUser(client)

def UserControl(user_server_port, user_server_ip, user_certfile, user_keyfile):
    usercontrolserver = UserControlServer(user_server_port, user_server_ip, user_certfile, user_keyfile)
    usercontrolserver.start()

def NodeControl(node_server_port, node_server_ip, node_certfile, node_keyfile):
    nodecontrolserver = NodeControlServer(node_server_port, node_server_ip, node_certfile, node_keyfile)
    nodecontrolserver.start()

def main():
    workingdir = os.getcwd()
    user_server_ip = 'localhost'
    user_server_port = 12345
    print(workingdir)

    user_certfile = '../../certfile.pem'
    user_keyfile = '../../keyfile.pem'

    node_server_ip = 'localhost'
    node_server_port = 12346

    node_certfile = '../../certfile.pem'
    node_keyfile = '../../keyfile.pem'
    print(user_certfile)
    print(node_keyfile)

    usercontrolthread = Process(target=UserControl, args=(user_server_port, user_server_ip, user_certfile, user_keyfile))
    usercontrolthread.start()

    nodecontrolthread = Process(target=NodeControl, args=(node_server_port, node_server_ip, node_certfile, node_keyfile))
    nodecontrolthread.start()



    while True:
        try :
            sleep(0.01)
        except KeyboardInterrupt:
            break





if __name__ == "__main__":
    main()