import time
from threading import Thread

import sys
import os

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Server.Master.InternalLibs.Server import *
from Server.Master.InternalLibs.Queue import BidirectionalQueue
from Server.Master.InternalLibs.Nodes import LoadBalancer
import uuid


import json
# import ssl

def gen_uid():
    return str(uuid.uuid4())

class Node:
    def __init__(self, uid, clientobject, pipe, data_server):
        self.__uid = uid
        self.__clientObject = clientobject
        self.__pipe = pipe
        self.running = True
        self.__data_server = data_server
        self.__load = None
        self.__refresh_load_counter = 0
        self.__tries = 0
        self.languages = {}

    def __send(self, data):
        self.__clientObject.send(data)

    def __get_last_message(self):
        return self.__clientObject.get_last_message()

    def main(self):
        self.get_load()
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
        # print("Got message from node:", message)
        obj = json.loads(message)
        if obj['command'] == 'greet':
            self.__sendUid()
        elif obj['command'] == 'bye':
            if obj['data'] == self.__uid:
                self.__eject()
        elif obj['command'] == 'ping':
            self.__pong()
        elif obj['command'] == 'PayloadExecuted':
            self.__pipe.send_to_server(json.dumps({"Status": "PayloadExecuted", "uid": obj['uid']}))
        elif obj['command'] == 'Load':
            self.__load = obj['load']
            self.__tries = 0
        elif obj['command'] == 'Languages':
            self.languages = obj['languages']



    def __sendUid(self):
        self.__send(json.dumps({"command": "uidIs", "uid": self.__uid}).encode('utf-8'))
        # self.__pipe.send(f"Node {self.__uid} sent greetings !")

    def __pong(self):
        self.__send(json.dumps({"command": "pong"}).encode('utf-8'))
        # self.__pipe.send(f"Node {self.__uid} sent ping")

    def __eject(self):
        try :
            self.__send(json.dumps({"command": "OUT", "data": "Goodbye"}).encode('utf-8'))
        except:
            pass
        self.running = False
        self.__clientObject.close()
        # self.__pipe.send(f"Node {self.__uid} ejected")
        # print(f"Node {self.uid} ejected")

    def __messages(self):
        data = self.__get_last_message()
        if data:
            return data
        else:
            return None

    def get_load(self):
        try :
            self.__send(json.dumps({"command": "getLoad"}).encode('utf-8'))
        except:
            print("Node DEAD !")
            self.__eject()
        self.__tries += 1
        if self.__tries > 3:
            print(f"Node {self.__uid} is not responding, ejecting")
            self.__eject()

    def prepare_data_session(self, user_uid, key):
        print("Asking node to prepare data session")
        self.__send(json.dumps({"command": "DataSession", "server" : self.__data_server, "user_uid": user_uid, "key": key}).encode('utf-8'))

    def close(self):
        self.__clientObject.close()


    def has_packages(self, packages : str):
        self.get_languages()
        tries = 0

        while len(self.languages) == 0 and tries < 10:
            time.sleep(0.1)

        if packages.lower() in self.languages:
            return self.languages[packages.lower()]

    def get_languages(self):
        self.__send(json.dumps({"command": "getLanguages"}).encode('utf-8'))

    @property
    def uid(self):
        return self.__uid

    @property
    def load(self) -> int:
        return self.__load


class NodesBook: # stores all nodes and interact with the load balancer algorithm
    def __init__(self, dataserver_ip, dataserver_port):
        # nodes are stored in the balancer
        self.running = True
        self.__Balancer = LoadBalancer.Balancer()
        self.__dataserver_ip = dataserver_ip
        self.__dataserver_port = dataserver_port

    def addNode(self, ssl_client):
        node_uid = gen_uid()
        bidiqeue = BidirectionalQueue()
        node = Node(node_uid, ssl_client, bidiqeue, (self.__dataserver_ip, self.__dataserver_port))

        node_thread = Thread(target=node.main)
        self.__Balancer.nodes[node.uid] = [node, node_thread, bidiqeue]
        self.__Balancer.nodes[node.uid][1].start()

    def removeNode(self, uid):
        del self.__Balancer.nodes[uid]


    def getNodes(self):
        return self.__Balancer.nodes

    def prepare_node_for(self, required_packages, user_uid, key):
        node = self.__Balancer.choose_node(required_packages)
        print(f"Node {node.uid} was chosen")
        node.prepare_data_session(user_uid, key)
        return node.uid

    def relay_to_node(self, uid, data):
        self.__Balancer.nodes[uid][2].send_to_client(data)

    def relay_from_node(self, uid):
        if self.__Balancer.nodes[uid][2].poll_from_client():
            return self.__Balancer.nodes[uid][2].recv_from_client()
        else:
            return None

    def refresh_load(self, uid):
        self.__Balancer.nodes[uid][0].get_load()

    def relay(self):
        buffer = []
        for uid in self.__Balancer.nodes:
            data = self.relay_from_node(uid)
            if data:
                buffer.append((uid, data))
        return buffer

    def refresh_all_load(self):
        for uid in self.__Balancer.nodes:
            self.refresh_load(uid)




class NodeControlServer(Server):
    def __init__(self, listener_port, listener_ip, certfile, keyfile, pipe, dataserver_ip, dataserver_port):
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        self.__dataserver = (dataserver_ip, dataserver_port)
        super().__init__(listener_port, "0.0.0.0", self.__callback, use_ssl=True, certfile=certfile, keyfile=keyfile)
        self.nodesBook = NodesBook(dataserver_ip, dataserver_port)
        self.__pipe = pipe
        self.__pipeListenerThread = Thread(target=self.__loop)
        self.running = True
        self.__refresh_load_counter = 0

    def start(self):
        print("Node control server starting on", self.__listener_ip, ":", self.__listener_port)
        self.__pipeListenerThread.start()
        super().start()

    def __callback(self, ssl_client):
        print("New node connected")
        self.nodesBook.addNode(ssl_client)

    def __loop(self):
        print("Node control server pipe listener started")
        while self.running:
            if self.__pipe.poll_from_server():
                message = self.__pipe.recv_from_server()
                print(f"-Message for nodecontrolserver: {message}")
                if "DataSessionRequest" in message:
                    obj = json.loads(message)
                    nodeuid = self.nodesBook.prepare_node_for(obj['required_packages'], obj['uid'], obj['Key'])
                    self.__pipe.send_to_server(json.dumps({"command": "NodePrepared", "uids": (obj['uid'], nodeuid)}))

            data = self.nodesBook.relay()
            if len(data) > 0:
                for i in data:
                    self.__pipe.send_to_server(i[1])

            self.__refresh_load_counter += 1
            if self.__refresh_load_counter > 200:
                self.nodesBook.refresh_all_load()
                self.__refresh_load_counter = 0
            try :
                for uid in self.nodesBook.getNodes():
                    if self.nodesBook.getNodes()[uid][0].running == False:
                        self.nodesBook.removeNode(uid)
                        print(f"Node {uid} removed")
                        self.__pipe.send_to_server(json.dumps({"command": "NodeRemoved", "uid": uid}))
            except RuntimeError:
                pass

            time.sleep(0.005)



