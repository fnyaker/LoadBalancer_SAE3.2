from Server import Server
import uuid

class NodeControlServer(Server): # this class is the one that listen for new nodes
    """The server class that listens for new nodes.
    It will manage them and allow them to connect to the master server and exchange the encryption key to connect to the user"""

    def __init__(self, listener_port, listener_ip, certfile, keyfile):
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl= True, certfile= certfile, keyfile= keyfile)
        nodes = {}

    def __genNodeUid(self):
        return str(uuid.uuid4())

    def __callback(self, ssl_client, addr):
        print("New node connected")
        node_uid = self.__genNodeUid()