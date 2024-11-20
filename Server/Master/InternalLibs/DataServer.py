import time


from Server.Master.InternalLibs.Server import Server
from cryptography.fernet import Fernet



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
        auth_pass = False
        remaining = 3
        while not auth_pass and remaining > 0:
            data = clientObject.get_last_message()
            if data:
                for i in self.__authorised_client:
                    decrypted = self.__decrypt(data, i[1])
                    if decrypted == i[0]:
                        auth_pass = True
                        break
            remaining -= 1

        return auth_pass


    def __decrypt(self, data, key:str):
        cypher = Fernet(key.encode('utf-8'))

        return cypher.decrypt(data).decode('utf-8')

class DataServer:
    """The base class for other server classes"""

    def __init__(self, userlisten_ip, userlisten_port, node_listen_ip, node_listen_port, pipe):
        self.__userListener = Listener(userlisten_ip, userlisten_port)
        self.__nodeListener = Listener(node_listen_ip, node_listen_port)

    def start(self):
        self.__userListener.start()
        self.__nodeListener.start()

    def __new_user(self, clientObject):
        pass