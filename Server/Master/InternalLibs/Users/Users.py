import time
from threading import Thread


import json
# import ssl


class User: # user class for the control connection
    def __init__(self, uid, clientobject):
        self.__uid = uid
        self.__clientObject = clientobject
        self.running = True
        # self.__handlerThread = Thread(target=self.handle)

    def __send(self, data):
        self.__clientObject.send(data)

    def __get_last_message(self):
        return self.__clientObject.get_last_message()

    def main(self):
        try:
            while self.running:
                self.__loop()
                time.sleep(0.001)
                # print("User management loop")
        except KeyboardInterrupt:
            self.close()

    def __loop(self):
        try:
            msg = self.__messages()
            # time.sleep(0.01)
            if msg:
                self.__handleClientMessage(msg)
            else:
                pass
        except RuntimeError:
            pass
        time.sleep(0.01)

    def __handleClientMessage(self, message):
        print("Got message from user :", message)
        obj = json.loads(message)
        if obj['command'] == 'greet':
            self.__sendUid()
        elif obj['command'] == 'bye':
            if obj['data'] == self.uid:
                self.__eject()
        elif obj['command'] == 'ping':
            self.__pong()

    def __sendUid(self):
        self.__send(json.dumps({"command": "uidIs", "uid": self.uid}).encode('utf-8'))

    def __pong(self):
        self.__send(json.dumps({"command": "pong"}).encode('utf-8'))

    def __eject(self):
        self.__send(json.dumps({"command": "OUT", "data": "Goodbye"}).encode('utf-8'))
        self.running = False
        print(f"User {self.uid} ejected")

    def __messages(self):
        # if there are messages, return the first one and remove it from the list
        data = self.__get_last_message()
        # print(data)
        if data:
            return data
        else:
            return None

    def close(self):
        self.__clientObject.close()

    @property
    def uid(self):
        return self.__uid


class UserBook: # stores all users and allow them to interact with outside
    def __init__(self):
        self.__users = {}
        self.running = True

    def addUser(self, user):
        # self.__users[user.uid] = user
        # we create a new thread for that user to listen for messages and respond
        userthread = Thread(target=user.main)
        self.__users[user.uid] = [user,userthread]
        self.__users[user.uid][1].start()

    def removeUser(self, uid):
        del self.__users[uid]

    def getUser(self, uid):
        return self.__users[uid]

    def getUsers(self):
        return self.__users