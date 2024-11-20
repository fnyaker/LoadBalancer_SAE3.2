import time
from threading import Thread
from Server.Master.InternalLibs.Server import Server
from cryptography.fernet import Fernet

import uuid

import json


# import ssl

def gen_uid():
    return str(uuid.uuid4())


def generate_encryption_key():
    """
    Génère une clé de chiffrement symétrique.
    Retourne la clé sous forme de chaîne de caractères.
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')


class User:
    def __init__(self, uid, clientobject, pipe, data_session):
        self.__data_session = data_session
        self.__uid = uid
        self.__clientObject = clientobject
        self.__pipe = pipe
        self.running = True

    def __send(self, data):
        self.__clientObject.send(data)

    def __get_last_message(self):
        return self.__clientObject.get_last_message()

    def main(self):
        try:
            while self.running:
                self.__loop()
                time.sleep(0.001)
        except KeyboardInterrupt:
            self.close()

    def __loop(self):
        try:
            msg = self.__messages()
            if msg:
                self.__handleClientMessage(msg)
            else:
                pass
        except RuntimeError:
            pass
        time.sleep(0.01)

    def __handleClientMessage(self, message):
        # print("Got message from user:", message)
        obj = json.loads(message)
        if obj['command'] == 'greet':
            self.__sendUid()
        elif obj['command'] == 'bye':
            if obj['data'] == self.__uid:
                self.__eject()
        elif obj['command'] == 'ping':
            self.__pong()
        elif obj['command'] == 'initDataSession':
            self.__start_data_session()

    def __sendUid(self):
        self.__send(json.dumps({"command": "uidIs", "uid": self.__uid}).encode('utf-8'))
        self.__pipe.send(f"User {self.__uid} sent greetings !")

    def __pong(self):
        self.__send(json.dumps({"command": "pong"}).encode('utf-8'))
        self.__pipe.send(f"User {self.__uid} sent ping")

    def __eject(self):
        self.__send(json.dumps({"command": "OUT", "data": "Goodbye"}).encode('utf-8'))
        self.running = False
        self.__pipe.send(f"User {self.__uid} ejected")
        # print(f"User {self.uid} ejected")

    def __messages(self):
        data = self.__get_last_message()
        if data:
            return data
        else:
            return None

    def __start_data_session(self):
        self.__send(json.dumps({"command": "initDataSession", "data": self.__data_session}).encode('utf-8'))


        self.__send(json.dumps({}))

    def close(self):
        self.__clientObject.close()

    @property
    def uid(self):
        return self.__uid


class UserBook:  # stores all users and allow them to interact with outside
    def __init__(self):
        self.__users = {}
        self.running = True

    def addUser(self, user):
        # we create a new thread for that user to listen for messages and respond
        userthread = Thread(target=user.main)
        self.__users[user.uid] = [user, userthread]
        self.__users[user.uid][1].start()

    def removeUser(self, uid):
        del self.__users[uid]

    def getUser(self, uid):
        return self.__users[uid]

    def getUsers(self):
        return self.__users


class UserControlServer(Server):
    def __init__(self, listener_port, listener_ip, certfile, keyfile, pipe, dataServer_address, dataServer_port):
        self.__dataServer = (dataServer_address, dataServer_port)
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl=True, certfile=certfile, keyfile=keyfile)
        self.__userBook = UserBook()
        self.__pipe = pipe

    def start(self):
        # print("User control server starting on", self.__listener_ip, ":", self.__listener_port)
        super().start()

    def __callback(self, ClientObject):  # we create the user and already prepare for a data session
        client_uid = gen_uid()
        data_session = self.__prepare_data_session()
        client = User(client_uid, ClientObject, self.__pipe, data_session)
        # print("New user connected with uid", client_uid)
        self.__userBook.addUser(client)
        self.__pipe.send(f"NewUser'{client_uid}',Key'{data_session[1]}'")

    def __prepare_data_session(self):
        key = generate_encryption_key()
        return self.__dataServer, key
