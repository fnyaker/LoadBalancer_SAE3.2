from InternalLibs.Users.Users import *
from InternalLibs.Nodes.Nodes import *
from InternalLibs.Server import *
from InternalLibs.DataServer import *
import socket
import uuid
from time import sleep
import os

from multiprocessing import Process, Pipe




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

        self.user_pipe, self.node_pipe = Pipe()

    def start_user_control(self):
        usercontrolserver = UserControlServer(self.user_server_port, self.user_server_ip, self.user_certfile, self.user_keyfile, self.user_pipe)
        usercontrolserver.start()

    def start_node_control(self):
        nodecontrolserver = NodeControlServer(self.node_server_port, self.node_server_ip, self.node_certfile, self.node_keyfile, self.node_pipe)
        nodecontrolserver.start()

    def start_data_server(self):
        pass

    def __handle_messages(self,msg):
        pass

    def main(self):
        workingdir = os.getcwd()
        print(workingdir)
        print(self.user_certfile)
        print(self.node_keyfile)

        usercontrolthread = Process(target=self.start_user_control)
        usercontrolthread.start()

        nodecontrolthread = Process(target=self.start_node_control)
        nodecontrolthread.start()

        try:
            while True:
                if self.user_pipe.poll():
                    message = self.user_pipe.recv()
                    print(f"Message from UserControlServer: {message}")
                if self.node_pipe.poll():
                    message = self.node_pipe.recv()
                    print(f"Message from NodeControlServer: {message}")
                sleep(0.01)
        except KeyboardInterrupt:
            usercontrolthread.terminate()
            nodecontrolthread.terminate()

if __name__ == "__main__":
    manager = ServerManager()
    manager.main()