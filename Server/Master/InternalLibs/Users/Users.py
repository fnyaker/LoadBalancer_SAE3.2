import time
from threading import Thread
from Server.Master.InternalLibs.Server import Server
from cryptography.fernet import Fernet
from Server.Master.InternalLibs.Queue import BidirectionalQueue

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
        self.nodeuid = None
        self.__alive_tries = 0
        self.__alive_cnt = 0

    def __send(self, data):
        self.__clientObject.send(data)

    def __get_last_message(self):
        return self.__clientObject.get_last_message()

    def main(self):
        try:
            while self.running:
                self.__loop()
                time.sleep(0.01)
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

    def check_alive(self):
        try :
            self.__send(json.dumps({"command": "ping"}).encode('utf-8'))
        except:
            print("User DEAD !")
            self.__eject()
        self.__alive_tries += 1
        time.sleep(0.01)
        if self.__alive_tries > 3:
            print("User DEAD !")
            self.__eject()



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
        elif obj['command'] == 'pong':
            self.__alive_tries = 0
        elif obj['command'] == 'initDataSession':
            self.__start_data_session(obj["RequiredPackages"])
        elif obj['command'] == 'EndDataSession':
            self.__pipe.send_to_server(json.dumps({"Status": "PayloadExecuted", "uid": self.__uid}))
            self.nodeuid = None

    def __sendUid(self):
        self.__send(json.dumps({"command": "uidIs", "uid": self.__uid}).encode('utf-8'))

    def __pong(self):
        self.__send(json.dumps({"command": "pong"}).encode('utf-8'))

    def __eject(self):
        try :
            self.__send(json.dumps({"command": "OUT", "data": "Goodbye"}).encode('utf-8'))
        except:
            pass
        self.running = False
        self.__pipe.send_to_server(json.dumps({"Status": "UserEjected", "uid": self.__uid}))
        # print(f"User {self.uid} ejected")

    def __messages(self):
        data = self.__get_last_message()
        if data:
            return data
        else:
            return None

    def __start_data_session(self, RequiredPackages):
        self.__pipe.send_to_server(json.dumps({"DataSessionRequest": RequiredPackages, "uid": self.__uid, "Key": self.__data_session[1]}))
        self.__send(json.dumps({"command": "DataSession", "data": {
            "ip": self.__data_session[0][0],
            "port": self.__data_session[0][1],
            "key": self.__data_session[1]

        }}).encode('utf-8'))

    def end_data_session(self):
        print("Telling user to end data session")
        self.__send(json.dumps({"command": "EndDataSession"}).encode('utf-8'))
        self.nodeuid = None


    def close(self):
        self.__clientObject.close()

    @property
    def uid(self):
        return self.__uid


class UserBook:  # stores all users and allow them to interact with outside
    def __init__(self):
        self.__users = {}
        self.running = True

    def addUser(self, user, bidiqu):
        # we create a new thread for that user to listen for messages and respond
        userthread = Thread(target=user.main)
        self.__users[user.uid] = [user, userthread, bidiqu]
        self.__users[user.uid][1].start()

    def update_user_node(self, uids):
        self.__users[uids[0]][0].nodeuid = uids[1]


    def removeUser(self, uid):
        del self.__users[uid]

    def getUser(self, uid):
        return self.__users[uid]

    def getUsers(self):
        return self.__users

    def list_users(self):
        return self.__users.keys()

    def find_who_has_node(self, nodeuid):
        useruids = []
        for uid in self.__users:
            if self.__users[uid][0].nodeuid == nodeuid:
                print("User", uid, "has the node")
                useruids.append(uid)
        return useruids

    def tell_user_to_end_data_session(self, uid):

        self.__users[uid][0].end_data_session()

    def getqueufromuser(self, uid):
        if uid in self.__users:
            if self.__users[uid][2].poll_from_client():
                return self.__users[uid][2].recv_from_client()
            else:
                return None
        else:
            return None

    def checkAliveUsers(self):
        for uid in self.__users:
            self.__users[uid][0].check_alive()

    def searchDeadUsers(self):
        for uid in self.__users:
            if not self.__users[uid][0].running:
                self.removeUser(uid)
                print(f"User {uid} removed")
            else:
                pass


class UserControlServer(Server):
    def __init__(self, listener_port, listener_ip, certfile, keyfile, pipe, dataServer_address, dataServer_port):
        self.__dataServer = (dataServer_address, dataServer_port)
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        super().__init__(listener_port, listener_ip, self.__callback, use_ssl=True, certfile=certfile, keyfile=keyfile)
        self.__userBook = UserBook()
        self.__pipe = pipe
        self.checkalivecounter = 0


    def start(self):
        # print("User control server starting on", self.__listener_ip, ":", self.__listener_port)
        super().start()
        self.main()

    def main(self):
        while self.__userBook.running:
            if self.__pipe.poll_from_server():
                print("User control server Got message from server")
                message = self.__pipe.recv_from_server()
                obj = json.loads(message)
                print("User control server got", obj)
                #if "PayloadExecuted" in obj:
                #    self.__userBook.tell_user_to_end_data_session(obj["uid"])
                #elif "NodePrepared" in obj:
                #    self.__userBook.update_user_node(obj["uids"])
#
                #elif "NodeRemoved" in obj:
                #    print("Oh ! A node has been removed, i will see who was using it")
                #    useruids = self.__userBook.find_who_has_node(obj["uid"])
                #    for uid in useruids:
                #        self.__userBook.tell_user_to_end_data_session(uid)

                if "command" in obj:
                    if obj["command"] == "PayloadExecuted":
                        self.__userBook.tell_user_to_end_data_session(obj["uid"])
                    elif obj["command"] == "NodePrepared":
                        print("Node prepared by data server")
                        self.__userBook.update_user_node(obj["uids"])
                    elif obj["command"] == "NodeRemoved":
                        print("Oh ! A node has been removed, i will see who was using it")
                        useruids = self.__userBook.find_who_has_node(obj["uid"])
                        for uid in useruids:
                            self.__userBook.tell_user_to_end_data_session(uid)

            for uid in self.__userBook.list_users():
                data = self.__userBook.getqueufromuser(uid)
                if data:
                    self.__pipe.send_to_server(data)

            self.checkalivecounter += 1
            if self.checkalivecounter > 200:
                self.checkalivecounter = 0
                try :
                    self.__userBook.checkAliveUsers()
                    self.__userBook.searchDeadUsers()
                except RuntimeError:
                    pass
            time.sleep(0.005)


    def __callback(self, ClientObject):  # we create the user and already prepare for a data session
        client_uid = gen_uid()
        data_session = self.__prepare_data_session()
        bidiqu = BidirectionalQueue()
        client = User(client_uid, ClientObject, bidiqu, data_session)
        # print("New user connected with uid", client_uid)
        self.__userBook.addUser(client, bidiqu)
        # print(f"New user connected with uid {client_uid} [printed]")

    def __prepare_data_session(self):
        key = generate_encryption_key()
        return self.__dataServer, key

