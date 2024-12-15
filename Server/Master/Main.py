import sys
import os

# Ajouter le répertoire parent au sys.path


try :
    from libs.Users import *
    from libs.Nodes import *
    from libs.Server import *
    from libs.DataServer import *
    from libs.Queue import BidirectionalQueue
    print("Master Server Running packaged/prod version")
    import config
    usercertfilepath = "usercertfile.pem"
    userkeyfilepath = "userkeyfile.pem"

    nodecertfilepath = "nodecertfile.pem"
    nodekeyfilepath = "nodekeyfile.pem"


except ImportError:
    print("Master Server Running dev version ONLY ON UNIX")
    certfilepath = "../../certfile.pem"
    keyfilepath = "../../keyfile.pem"


    usercertfilepath = certfilepath
    userkeyfilepath = keyfilepath

    nodecertfilepath = certfilepath
    nodekeyfilepath = keyfilepath

    import config

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from InternalLibs.Users.Users import *
    from InternalLibs.Nodes.Nodes import *
    # from InternalLibs.Server import *
    from InternalLibs.DataServer import DataServer


from time import sleep
from multiprocessing import Process, Queue




class ServerManager:
    def __init__(self):

        self.user_pipe = BidirectionalQueue()
        self.node_pipe = BidirectionalQueue()
        self.dataserv_pipe = BidirectionalQueue()

        self.__users = []
        self.__nodes = []
        self.__data_sessions = []
        # self.loadbalancer_pipe = BidirectionalQueue()

    def start_user_control(self):
        usercontrolserver = UserControlServer(config.Users.listener_port, config.Users.listener_address, usercertfilepath, userkeyfilepath, self.user_pipe, config.Users.dataserver_external_address, config.Users.dataserver_external_port)
        usercontrolserver.start()

    def start_node_control(self):
        nodecontrolserver = NodeControlServer(config.Nodes.listener_port, config.Nodes.listener_address, nodecertfilepath, nodekeyfilepath, self.node_pipe, config.Nodes.dataserver_external_address, config.Nodes.dataserver_external_port)
        nodecontrolserver.start()

    def start_data_server(self):
        dataserver = DataServer(config.Users.dataserver_listener_address, config.Users.dataserver_listener_port, config.Nodes.dataserver_listener_address, config.Nodes.dataserver_listener_port, self.dataserv_pipe)
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
            if obj["command"] == "NoNodeAvailable":
                print("No node available")
                self.user_pipe.send_to_client(json.dumps({"command": "NoNodeAvailable", "uid": obj["uid"]}))
                self.dataserv_pipe.send_to_client(json.dumps({"command": "PayloadExecuted", "uid": obj["uid"]}))



    def main(self):
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
                sleep(0.005)
        except KeyboardInterrupt:
            try :
                usercontrolprocess.terminate()
            except:
                pass
            try:
                nodecontrolProcess.terminate()
            except:
                pass
            try:
                dataservprocess.terminate()
            except:
                pass

if __name__ == "__main__":
    manager = ServerManager()
    manager.main()