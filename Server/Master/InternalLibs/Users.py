from .Server import Server
import uuid


class User:
    def __init__(self, uid, clientobject):
        self.__uid = uid
        self.__clientObject = clientobject

    def send(self, data):
        self.__clientObject.send(data)

    def get_last_message(self):
        return self.__clientObject.get_last_message()

    def close(self):
        self.__clientObject.close()


class UserStore: # this is the store that will keep track of all the users and manage them
    def __init__(self):
        self.__users = {}

    def addUser(self, user):
        self.__users[user.uid] = user
        # we create a new thread for that user to listen for messages

    def removeUser(self, uid):
        del self.__users[uid]

    def getUser(self, uid):
        return self.__users[uid]

    def getUsers(self):
        return self.__users

class UserControlServer(Server): # this class is the one that listen for new users
    """The server class that listens for new users.
    It will manage them and allow them to get the key to connect to the node, it must be encrypted
    A second UserServer will be created for the master serve to serve as a relay between the user and the node"""
    def __init__(self, listener_port, listener_ip, certfile, keyfile):
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl= True, certfile= certfile, keyfile= keyfile)
        self.__UserManagement = UserStore()

    def __genClientUid(self):
        return str(uuid.uuid4())

    def __callback(self, ClientObject):
        print("New user connected")
        client_uid = self.__genClientUid()
        client = User(client_uid, ClientObject)

