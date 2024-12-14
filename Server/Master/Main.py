import sys
import os

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from InternalLibs.Users.Users import *
from InternalLibs.Nodes.Nodes import *
from InternalLibs.Server import *
from InternalLibs.DataServer import *
import socket
import uuid
from time import sleep
from InternalLibs.Queue import BidirectionalQueue

from multiprocessing import Process, Queue




class ServerManager:
    def __init__(self):
        self.user_server_ip = 'server'
        self.user_server_port = 12345
        self.user_certfile = '../../certfile.pem'
        self.user_keyfile = '../../keyfile.pem'

        self.node_server_ip = 'server'
        self.node_server_port = 12346
        self.node_certfile = '../../certfile.pem'
        self.node_keyfile = '../../keyfile.pem'

        self.dataServer_user_ip = 'server'
        self.dataServer_user_port = 22345

        self.dataServer_node_ip = 'server'
        self.dataServer_node_port = 22346

        self.user_pipe = BidirectionalQueue()
        self.node_pipe = BidirectionalQueue()
        self.dataserv_pipe = BidirectionalQueue()
        # self.loadbalancer_pipe = BidirectionalQueue()

    def start_user_control(self):
        usercontrolserver = UserControlServer(self.user_server_port, self.user_server_ip, self.user_certfile, self.user_keyfile, self.user_pipe, self.dataServer_user_ip, self.dataServer_user_port)
        usercontrolserver.start()

    def start_node_control(self):
        nodecontrolserver = NodeControlServer(self.node_server_port, self.node_server_ip, self.node_certfile, self.node_keyfile, self.node_pipe, self.dataServer_node_ip, self.dataServer_node_port)
        nodecontrolserver.start()

    def start_data_server(self):
        dataserver = DataServer("0.0.0.0", self.dataServer_user_port, "0.0.0.0", self.dataServer_node_port, self.dataserv_pipe)
        dataserver.start()


    def start_load_balancer(self):
        pass

    def handle_user_message(self, message):
        obj = json.loads(message)
        print("Main Process got ",obj)
        if "DataSessionRequest" in obj:
            print("Asking the data server for a data session")
            self.dataserv_pipe.send_to_client(json.dumps({"command" : "DataSessionRequest", "uid": obj["uid"], "Key": obj["Key"]}))
            self.node_pipe.send_to_client(json.dumps({"command": "DataSessionRequest", "uid": obj["uid"], "Key": obj["Key"], "required_packages": obj["DataSessionRequest"]}))
            print("Data session request sent")

    def handle_node_message(self, message):
        obj = json.loads(message)
        print("Main Process got ",obj)
        if "Status" in obj:
            print("Status message from node")
            if obj["Status"] == "PayloadExecuted":
                print("Payload executed")
                self.dataserv_pipe.send_to_client(json.dumps({"command": "PayloadExecuted", "uid": obj["uid"]}))
                self.user_pipe.send_to_client(json.dumps({"command": "PayloadExecuted", "uid": obj["uid"]}))

        if "command" in obj:
            if obj["command"] == "NodeRemoved":
                print("Node removed")
                self.dataserv_pipe.send_to_client(json.dumps({"command": "NodeRemoved", "uid": obj["uid"]}))
                self.user_pipe.send_to_client(json.dumps({"command": "NodeRemoved", "uid": obj["uid"]}))
            if obj["command"] == "NodePrepared":
                print("Node prepared")
                self.user_pipe.send_to_client(json.dumps({"command": "NodePrepared", "uids": obj["uids"]}))
                self.dataserv_pipe.send_to_client(json.dumps({"command": "NodePrepared", "uids": obj["uids"]}))


    def main(self):
        workingdir = os.getcwd()
        print(workingdir)
        print(self.user_certfile)
        print(self.node_keyfile)

        usercontrolprocess = Process(target=self.start_user_control)
        usercontrolprocess.start()

        nodecontrolProcess = Process(target=self.start_node_control)
        nodecontrolProcess.start()

        dataservprocess = Process(target=self.start_data_server)
        dataservprocess.start()

        try:
            while True:
                if self.user_pipe.poll_from_client():
                    message = self.user_pipe.recv_from_client()
                    print(f"Message from UserControlServer: {message}")
                    self.handle_user_message(message)
                if self.node_pipe.poll_from_client():
                    message = self.node_pipe.recv_from_client()
                    print(f"Message from NodeControlServer: {message}")
                    self.handle_node_message(message)
                if self.dataserv_pipe.poll_from_client():
                    message = self.dataserv_pipe.recv_from_client()
                    print(f"Message from DataServer: {message}")
                sleep(0.01)
        except KeyboardInterrupt:
            usercontrolprocess.terminate()
            nodecontrolProcess.terminate()

if __name__ == "__main__":
    manager = ServerManager()
    manager.main()