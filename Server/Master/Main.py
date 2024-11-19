from InternalLibs.Users.Users import *
from InternalLibs.Nodes.Nodes import *
from InternalLibs.Server import *

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

class UserControlServer(Server): # this class is the one that listen for new users
    """The server class that listens for new users.
    It will manage them and allow them to get the key to connect to the node, it must be encrypted
    A second UserServer will be created for the master serve to serve as a relay between the user and the node"""
    def __init__(self, listener_port, listener_ip, certfile, keyfile):
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl= True, certfile= certfile, keyfile= keyfile)
        self.__userBook = UserBook()

    def start(self):
        super().start()

    def __genClientUid(self):
        return str(uuid.uuid4())

    def __callback(self, ClientObject):
        client_uid = self.__genClientUid()
        client = User(client_uid, ClientObject)
        print("New user connected with uid", client_uid)
        self.__userBook.addUser(client)



def main():
    server_ip = 'localhost'
    server_port = 12345
    certfile = '../../certfile.pem'
    keyfile = '../../keyfile.pem'

    # Create and start the UserControlServer
    server = UserControlServer(listener_port=server_port, listener_ip=server_ip, certfile=certfile, keyfile=keyfile)
    server.start()
    print(f"Server started on {server_ip}:{server_port}")

    nodeserver = NodeControlServer(listener_port=server_port+1, listener_ip=server_ip, certfile=certfile, keyfile=keyfile)

    try:
        while True:
            pass  # Keep the server running
    except KeyboardInterrupt:
        print("Shutting down the server...")
        server.stop()

if __name__ == "__main__":
    main()