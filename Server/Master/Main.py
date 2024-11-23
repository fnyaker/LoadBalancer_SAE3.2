from InternalLibs.Users.Users import *
from InternalLibs.Nodes.Nodes import *
from InternalLibs.Server import *
from InternalLibs.DataServer import *
import socket
import uuid
from time import sleep
import os

from multiprocessing import Process, Queue

class BidirectionalQueue:
    def __init__(self):
        self.queue_to_server = Queue()
        self.queue_to_client = Queue()

    def send_to_server(self, data):
        self.queue_to_server.put(data)

    def recv_from_server(self):
        return self.queue_to_client.get()

    def poll_from_server(self, timeout=0):
        return not self.queue_to_client.empty()

    def send_to_client(self, data):
        self.queue_to_client.put(data)

    def recv_from_client(self):
        return self.queue_to_server.get()

    def poll_from_client(self, timeout=0):
        return not self.queue_to_server.empty()


class ServerManager:
    def __init__(self):
        self.user_server_ip = 'localhost'
        self.user_server_port = 12345
        self.user_certfile = '../../certfile.pem'
        self.user_keyfile = '../../keyfile.pem'

        self.node_server_ip = 'localhost'
        self.node_server_port = 12346
        self.node_certfile = '../../certfile.pem'
        self.node_keyfile = '../../keyfile.pem'

        self.dataServer_user_ip = 'localhost'
        self.dataServer_user_port = 22345

        self.dataServer_node_ip = 'localhost'
        self.dataServer_node_port = 22346

        self.user_pipe = BidirectionalQueue()
        self.node_pipe = BidirectionalQueue()
        self.dataserv_pipe = BidirectionalQueue()
        self.loadbalancer_pipe = BidirectionalQueue()

    def start_user_control(self):
        usercontrolserver = UserControlServer(self.user_server_port, self.user_server_ip, self.user_certfile, self.user_keyfile, self.user_pipe, self.dataServer_user_ip, self.dataServer_user_port)
        usercontrolserver.start()

    def start_node_control(self):
        nodecontrolserver = NodeControlServer(self.node_server_port, self.node_server_ip, self.node_certfile, self.node_keyfile, self.node_pipe)
        nodecontrolserver.start()

    def start_data_server(self):
        dataserver = DataServer(self.dataServer_user_ip, self.dataServer_user_port, self.dataServer_node_ip, self.dataServer_node_port, self.dataserv_pipe)
        dataserver.start()


    def start_load_balancer(self):
        pass

    def handle_user_message(self, message):
        obj = json.loads(message)
        print("Main Process got ",obj)
        if "DataSessionRequest" in obj:
            print("Asking the data server for a data session")
            self.dataserv_pipe.send_to_client(json.dumps({"command" : "DataSessionRequest", "uid": obj["uid"], "Key": obj["Key"]}))


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