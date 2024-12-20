#import sys
#import os

# Ajouter le répertoire parent au sys.path


import time
import json
from threading import Thread
from .Server import Server
from cryptography.fernet import Fernet
from multiprocessing import Process

class Session :
    """This class correspond to a user that
     is connected to the data server for
     compiling and running code in the cloud.
      The user stays the same but the node can change"""
    def __init__(self, UserObject, useruid = None):
        self.__clientObject = UserObject
        self.__user_uid =  useruid
        self.__node = None
        self.__relayProcess = None
        self.relaying = False
        self.dead = False


    def startRelay(self):
        self.__relayProcess = Process(target=self.__main)
        self.__relayProcess.start()

    def stopRelay(self):
        if self.__relayProcess is not None:
            self.__relayProcess.terminate()
            self.__relayProcess = None

    def restartRelay(self):
        self.stopRelay()
        self.startRelay()

    def __main(self):
        usernodeThread = Thread(target=self.__relay_usernode)
        nodetouserThread = Thread(target=self.__relay_nodetouser)
        self.relaying = True
        usernodeThread.start()
        nodetouserThread.start()
        usernodeThread.join()
        nodetouserThread.join()

        print("Relay process ended (should never happen)")


    def useNode(self, node):
        print("Node used")
        self.__node = node
        self.restartRelay()
        # self.__node.send(json.dumps({"command": "GOGOGO"}).encode('utf-8'))


    def __relay_usernode(self): # should never be called outside of the dedicated relay process
        while self.relaying:
            try :
                data = self.__clientObject.fast_get_last_message()
            except ConnectionResetError:
                print("User disconnected")
                break
            if data:
                #print("USER -> NODE")
                try :
                    self.__node.send(data)
                except BrokenPipeError:
                    print("Node disconnected")
                    break
                except ConnectionResetError:
                    print("Node disconnected")
                    break

        self.relaying = False
        self.dead = True

    def __relay_nodetouser(self): # should never be called outside of the dedicated relay process
        while self.relaying:
            try :
                data = self.__node.fast_get_last_message()
            except ConnectionResetError:
                print("Node disconnected")
                break
            if data:
                #print("NODE -> USER")
                try :
                    self.__clientObject.send(data)
                except BrokenPipeError:
                    print("User disconnected")
                    break
                except ConnectionResetError:
                    print("User disconnected")
                    break

        self.relaying = False


    @property
    def client_uid(self):
        return self.__user_uid





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
        time.sleep(0.1)
        print("Authenticating client")
        auth_pass = False
        remaining = 3
        print("Authorised clients:", self.__authorised_client)
        while not auth_pass and remaining > 0:
            print("Remaining tries:", remaining)
            data = clientObject.get_last_message()
            if data:
                for i in self.__authorised_client:
                    try :
                        decrypted = self.__decrypt(data, i[1])
                        print("Decrypted:", decrypted)
                        if decrypted == i[0]:
                            clientObject.send(self.__encrypt(json.dumps({"command" : "Auth_pass"}), i[1]))
                            auth_pass = True
                            break
                    except:
                        pass

            remaining -= 1

        if auth_pass:
            print("Client authorised")

            self.__callback(clientObject, decrypted)
        else:
            print("Client denied")
            clientObject.close()

    def start(self):
        super().start()
        print("Listener started")

    def add_authorised_client(self, uid, key):
        print("Adding authorised client")
        self.__authorised_client.append((uid, key))

    def rm_authorised_client(self, uid):
        for i in self.__authorised_client:
            print(i[0], uid)
            if i[0] == uid:
                print("Removing authorised client")
                self.__authorised_client.remove(i)
                break


    def __decrypt(self, data, key:str):
        cypher = Fernet(key.encode('utf-8'))

        return cypher.decrypt(data).decode('utf-8')

    def __encrypt(self, data, key:str):
        cypher = Fernet(key.encode('utf-8'))
        return cypher.encrypt(data.encode('utf-8'))

class DataServer:

    def __init__(self, userlisten_ip, userlisten_port, node_listen_ip, node_listen_port, pipe):
        self.__userListener = Listener(userlisten_ip, userlisten_port, self.__new_user)
        self.__nodeListener = Listener(node_listen_ip, node_listen_port, self.__new_node)
        self.__pipe = pipe
        self.__mainThread = Thread(target=self.__main)
        self.__nodes = [ # here there will be waiting nodes to be used (NodeObject, AssignedUserUid)

        ]
        self.__sessions = [

            ]
        self.__running = True


    def start(self):
        self.__userListener.start()
        self.__nodeListener.start()
        self.__mainThread.start()
        print("Data server started")


    def __new_user(self, clientObject, uid):
        self.__sessions.append(Session(clientObject, uid))
        print("New user connected with uid", uid)
        self.rescan_nodes()

    def __rm_user(self, uid):
        for i in self.__sessions:
            if i.client_uid == uid:
                i.stopRelay()
                self.__sessions.remove(i)
                self.__userListener.rm_authorised_client(uid)
                self.__nodeListener.rm_authorised_client(uid)
                break


    def rescan_nodes(self): # we redo the same thing as new node but for all wainting nodes
        for i in self.__nodes:
            self.__new_node(i[0], i[1], i[2])
            del i

    def __new_node(self, clientObject, uid, tries = 0):
        # we check if a session started by the user with the uid that is in the message is waiting
        for i in self.__sessions:
            if i.client_uid == uid and not i.dead:
                i.useNode(clientObject)
                break
        else:
            # print("Node not used")
            # we add the node to the waiting list
            if tries < 500:
                self.__nodes.append((clientObject, uid, tries + 1))
                time.sleep(0.02)

            else:
                print("Node unbale to connect or user id too slow")
                clientObject.close()




    def __main(self):
        while self.__running:
            self.__checkformsg()
            self.cleanup()
            time.sleep(0.01)

    def __checkformsg(self):
        # print("Checking for messages")
        if self.__pipe.poll_from_server():
            msg = self.__pipe.recv_from_server()
            if msg:
                print("DataServer got", msg)
                self.__handle_messages(msg)


    def __handle_messages(self,msg):
        obj = json.loads(msg)
        if "command" in obj:
            if obj["command"] == "DataSessionRequest":
                self.__userListener.add_authorised_client(obj["uid"], obj["Key"])
                self.__nodeListener.add_authorised_client(obj["uid"], obj["Key"])

            elif obj["command"] == "PayloadExecuted":
                print("relay stopping")
                for i in self.__sessions:
                    print(i.client_uid, obj["uid"])
                    if i.client_uid == obj["uid"]:
                        print("Stopping relay for user", obj["uid"])
                        self.__rm_user(obj["uid"])
                        self.__userListener.rm_authorised_client(obj["uid"])
