from threading import Thread
import time

class Node:
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
                # print("Node management loop")
        except KeyboardInterrupt:
            self.close()

    def __loop(self):
        try:
            msg = self.__messages()
            # time.sleep(0.01)
            if msg:
                self.__handleNodeMessage(msg)
            else:
                pass
        except RuntimeError:
            pass
        time.sleep(0.01)

    def __handleNodeMessage(self, message):
        pass

    def __messages(self):
        return self.__get_last_message()

    def close(self):
        self.__clientObject.close()



class NodesBook:
    def __init__(self):
        self.nodes = {}

    def addNode(self, node):
        self.nodes[node.uid] = node
        # we will create a new thread for that node to listen for messages and respond
        nodeThread = Thread(target=node.main)
        self.nodes[node.uid] = [node, nodeThread]
        self.nodes[node.uid][1].start()

    def removeNode(self, uid):
        del self.nodes[uid]

    def getNode(self, uid):
        return self.nodes[uid]

    def getNodes(self):
        return self.nodes
