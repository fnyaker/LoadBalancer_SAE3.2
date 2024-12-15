from Server.Master import config as master_config
import os
import shutil

# generation of 3 folders each containing all files they will need to run

class IO:
    def __init__(self):
        self.__os_type = os.name # nt or posix

    def translate_path(self, path):
        if self.__os_type == 'nt':
            return path.replace('/', '\\')
        else:
            return path.replace('\\', '/')

    def create_folder(self, path):
        path = self.translate_path(path)

        if not os.path.exists(path):
            # we must translate the path to the os type
            os.makedirs(path)
        else:
            print(f"Folder {path} already exists")

    def copy_file(self, src, dest):
        src = self.translate_path(src)
        dest = self.translate_path(dest)

        if os.path.exists(src):
            with open(src, 'rb') as f:
                with open(dest, 'wb') as f2:
                    f2.write(f.read())
        else:
            print(f"File {src} does not exist")

    def delete(self, path):
        path = self.translate_path(path)
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        else:
            print(f"Path {path} does not exist")



class Master(IO):
    def __init__(self):
        super().__init__()
        self.__config = master_config


    def generate(self):
        self.create_folder("Packages/Master")
        self.create_folder("Packages/Master/libs")

    def copy(self):
        self.copy_file("usercertfile.pem", "Packages/Master/usercertfile.pem")
        self.copy_file("userkeyfile.pem", "Packages/Master/userkeyfile.pem")
        self.copy_file("nodecertfile.pem", "Packages/Master/nodecertfile.pem")
        self.copy_file("nodekeyfile.pem", "Packages/Master/nodekeyfile.pem")
        self.copy_file("Server/Master/config.py", "Packages/Master/config.py")
        self.copy_file("Server/Master/Main.py", "Packages/Master/Main.py")
        self.copy_file("Server/Master/InternalLibs/Nodes/LoadBalancer.py", "Packages/Master/libs/LoadBalancer.py")
        self.copy_file("Server/Master/InternalLibs/Nodes/Nodes.py", "Packages/Master/libs/Nodes.py")
        self.copy_file("Server/Master/InternalLibs/Server.py", "Packages/Master/libs/Server.py")
        self.copy_file("Server/Master/InternalLibs/Queue.py", "Packages/Master/libs/Queue.py")
        self.copy_file("Server/Master/InternalLibs/Users/Users.py", "Packages/Master/libs/Users.py")
        self.copy_file("Server/Master/InternalLibs/DataServer.py", "Packages/Master/libs/DataServer.py")




class Node(IO):
    def __init__(self):
        super().__init__()

    def generate(self):
        self.create_folder("Packages/Node")
        self.create_folder("Packages/Node/libs")

    def copy(self):
        self.copy_file("nodecertfile.pem", "Packages/Node/nodecertfile.pem")
        # self.copy_file("nodekeyfile.pem", "Packages/Node/nodekeyfile.pem")
        self.copy_file("Server/Slave/config.py", "Packages/Node/config.py")
        self.copy_file("Server/Slave/Main.py", "Packages/Node/Main.py")
        self.copy_file("Server/Slave/runner.py", "Packages/Node/libs/runner.py")
        self.copy_file("Server/Master/InternalLibs/Queue.py", "Packages/Node/libs/Queue.py")



class User(IO):
    def __init__(self):
        super().__init__()

    def generate(self):
        self.create_folder("Packages/User")
        self.create_folder("Packages/User/libs")

    def copy(self):
        self.copy_file("usercertfile.pem", "Packages/User/usercertfile.pem")
        #self.copy_file("userkeyfile.pem", "Packages/User/userkeyfile.pem")
        self.copy_file("UserGui/libs/Backend.py", "Packages/User/libs/Backend.py")
        self.copy_file("UserGui/Main.py", "Packages/User/Main.py")

class SSLCerts:
    def __init__(self):
        self.__config = master_config

    def generate_user(self):
        print("Generating User SSL Certs")
        print("When you will be asked for the domain name, please enter the domain name you use to access the server externally from the user's perspective")
        nop = input("Press enter to continue")
        os.system("openssl genpkey -algorithm RSA -out userkeyfile.pem")
        os.system("openssl req -new -key userkeyfile.pem -out usercsr.pem")
        os.system("openssl req -x509 -key userkeyfile.pem -in usercsr.pem -out usercertfile.pem -days 365")

    def generate_node(self):
        print("Generating Node SSL Certs")
        print("When you will be asked for the domain name, please enter the domain name you use to access the server externally from the nodes")
        nop = input("Press enter to continue")
        os.system("openssl genpkey -algorithm RSA -out nodekeyfile.pem")
        os.system("openssl req -new -key nodekeyfile.pem -out nodecsr.pem")
        os.system("openssl req -x509 -key nodekeyfile.pem -in nodecsr.pem -out nodecertfile.pem -days 365")

    def clean(self):
        # os.remove("csr.pem")
        os.remove("nodecsr.pem")
        os.remove("usercsr.pem")

        os.remove("nodekeyfile.pem")
        os.remove("userkeyfile.pem")

        os.remove("nodecertfile.pem")
        os.remove("usercertfile.pem")




class Main(IO):
    def __init__(self):
        super().__init__()
        self.__master = Master()
        self.__node = Node()
        self.__user = User()
        self.__ssl = SSLCerts()

    def generate(self, update = False):
        if not update:
            self.__ssl.generate_user()
            self.__ssl.generate_node()
        self.create_folder('Packages')

        self.__master.generate()
        self.__node.generate()
        self.__user.generate()

        self.__master.copy()
        self.__node.copy()
        self.__user.copy()

        self.__ssl.clean()


    def run(self):
        self.generate()

    def update(self):
        self.copy_file("Packages/Master/config.py", "masterconfig.py")
        self.copy_file("Packages/Node/config.py", "nodeconfig.py")
        self.copy_file("Packages/Master/usercertfile.pem", "usercertfile.pem")
        self.copy_file("Packages/Master/userkeyfile.pem", "userkeyfile.pem")
        self.copy_file("Packages/Master/nodecertfile.pem", "nodecertfile.pem")
        self.copy_file("Packages/Master/nodekeyfile.pem", "nodekeyfile.pem")

        self.delete("Packages")
        self.generate(update = True)

if __name__ == '__main__':
    Packager = Main()
    Packager.run()