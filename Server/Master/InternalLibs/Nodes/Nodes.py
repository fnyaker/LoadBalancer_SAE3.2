import time
from threading import Thread


import json
# import ssl


class Node: # node class for the control connection
    def __init__(self, uid, clientobject):
        self.__uid = uid
        self.__clientObject = clientobject
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
        print("Got message from node:", message)
        obj = json.loads(message)
        if obj['command'] == 'greet':
            self.__sendUid()
        elif obj['command'] == 'bye':
            if obj['data'] == self.__uid:
                self.__eject()
        elif obj['command'] == 'ping':
            self.__pong()

    def __sendUid(self):
        self.__send(json.dumps({"command": "uidIs", "uid": self.__uid}).encode('utf-8'))

    def __pong(self):
        self.__send(json.dumps({"command": "pong"}).encode('utf-8'))

    def __eject(self):
        self.__send(json.dumps({"command": "OUT", "data": "Goodbye"}).encode('utf-8'))
        self.running = False
        print(f"Node {self.uid} ejected")

    def __messages(self):
        data = self.__get_last_message()
        if data:
            return data
        else:
            return None

    def close(self):
        self.__clientObject.close()

    @property
    def uid(self):
        return self.__uid


class NodesBook: # stores all nodes and allows them to interact with outside
    def __init__(self):
        self.__nodes = {}
        self.running = True

    def addNode(self, node):
        node_thread = Thread(target=node.main)
        self.__nodes[node.uid] = [node, node_thread]
        self.__nodes[node.uid][1].start()

    def removeNode(self, uid):
        del self.__nodes[uid]

    def getNode(self, uid):
        return self.__nodes[uid]

    def getNodes(self):
        return self.__nodes