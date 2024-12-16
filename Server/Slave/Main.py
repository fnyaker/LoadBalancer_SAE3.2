import sys
import os
import select
import psutil
import config



import ssl
import socket
import json
import time
from threading import Thread
from cryptography.fernet import Fernet
import multiprocessing

try :
    from libs.Queue import BidirectionalQueue
    from libs import runner
    print("Slave Running packaged/prod version")
except ImportError:
    print("Slave Running dev version")
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from Server.Master.InternalLibs.Queue import BidirectionalQueue
    import runner


import subprocess
import platform
import uuid

multiprocessing.set_start_method('fork')


class Client:
    """This is a base class"""
    def __init__(self, serverAddress = "server", serverPort = 12346, useSSL = False, certfile = None):
        self.__serverAddress = serverAddress
        self.__serverPort = serverPort

        self.__useSSL = useSSL
        self.__certfile = certfile

        self.__context = None
        self.__sock = None


        if self.__useSSL:
            self.__context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.__certfile)
            self.__context.check_hostname = False
            self.__context.verify_mode = ssl.CERT_NONE
            self.__sock = self.__context.wrap_socket(
                socket.create_connection((self.__serverAddress, self.__serverPort)),
                server_hostname=self.__serverAddress)
        else:
            self.__sock = socket.create_connection((self.__serverAddress, self.__serverPort))


    def send(self, data : bytes):
        if self.__useSSL:
            self.__sock.sendall(data)
        else:
            self.__sock.send(data)

    def receive(self, size : 2048):
        return self.__sock.recv(size)

    def close(self):
        self.__sock.close()

    @property
    def addr(self):
        return self.__sock.getpeername()

    @property
    def useSSL(self):
        return self.__useSSL

class ControlClient(Client): # this is the client for the control connection, it must use ssl
    def __init__(self, serverAddress = config.master_address, serverPort = config.master_port, certfile = None):
        super().__init__(serverAddress, serverPort, True, certfile)
        self.__clientspipe = BidirectionalQueue()
        self.running = True
        self.__uid = None
        self.startListener()
        self.pingtime = None
        self.__UserProcesses = [] # contains : (uid, ProcessObject)

        self.__max_processes = config.max_processes
        self.__absolute_max_processes = config.absolute_max_processes

    def __send (self, data : str):
        super().send(data.encode('utf-8'))

    def __listener(self):
        while self.running:
            try :
                print("Reading ...")
                data = self.receive(2048)
                print("Got data ? ", data)
            except ssl.SSLWantReadError:
                print("SSLWantReadError")
                continue
            if data:
                self.__handleMessages(data.decode('utf-8'))
            else:
                pass
            print("Trying to get data from clients pipe")
            while self.__clientspipe.poll_from_client():
                data = self.__clientspipe.recv_from_client()
                print("Got data from client pipe", data)
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    continue
                except TypeError:
                    continue
                if data['Status'] == 'PayloadExecuted':
                    print("Payload executed for user", data['uid'])
                    self.__send(json.dumps({"command": "PayloadExecuted", "uid": data['uid']}))

            print("Checking for finished processes")

    def loop(self):
        while self.running:
            for i in self.__UserProcesses:
                try :
                    i[1].join(0.01)
                except AssertionError:
                    pass

                if not i[1].is_alive():
                    print("User process finished")

                    self.__send(json.dumps({"command": "PayloadExecuted", "uid": i[0]}))
                    self.__UserProcesses.remove(i)
                    print("EndDataSession sent")
            time.sleep(0.01)


    def startListener(self):
        print("Starting listener")
        self.__listenerThread = Thread(target=self.__listener)
        self.__listenerThread.start()
        print("Listener started")

    def __handleMessages(self, data : str):
        print("Got message from server")
        obj = json.loads(data)
        if obj['command'] == 'uidIs':
            self.__uid = obj['uid']
        elif obj['command'] == 'OUT':
            self.running = False
        elif obj['command'] == 'pong':
            try :
                self.pingtime = time.time() - self.pingtime
                print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass
        elif obj['command'] == 'ping':
            self.__send(json.dumps({"command": "pong"}))

        elif obj['command'] == 'DataSession':
            if len(self.__UserProcesses) < self.__absolute_max_processes:
                self.__initDataSession(obj)

        elif obj['command'] == 'getLoad':
            self.__load()

        elif obj['command'] == 'getLanguages':
            self.__send(json.dumps({"command": "Languages", "languages": self.__get_languages()}))

        elif obj['command'] == "getUserCount":
            self.__send(json.dumps({"command": "UserCount", "count": len(self.__UserProcesses), "max": self.__max_processes, "absolute_max": self.__absolute_max_processes}))

    def __get_languages(self):
        try :
            subprocess.run(['gcc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            c = False
        else:
            c = True


        try :
            subprocess.run(['g++', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            cpp = False
        else:
            cpp = True

        try :
            subprocess.run(['javac', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            java = False
        else:
            java = True

        try :
            subprocess.run(['python3', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            try :
                subprocess.run(['python', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                python = False
            else:
                python = True
        else:
            python = True

        return {"c": c, "cpp": cpp, "java": java, "python": python}


    def __load(self):
        # we get cpu usage and memory usage
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.__send(json.dumps({"command": "Load", "load": {"cpu": cpu, "mem": mem}}))

    def __initDataSession(self, data):
        UserProcess = multiprocessing.Process(target=self.datasession, args=(data['user_uid'], data['key'], self.__clientspipe))
        self.__UserProcesses.append((data['user_uid'], UserProcess))
        # UserProcess.set_start_method("fork")
        UserProcess.start()
        print("User process started")

    def datasession(self, user_uid, key, clientpipe):
        UserSession = UserEnv(user_uid, key, clientpipe)
        print("User session finished")


    def requestUid(self):
        print("Requesting uid from server")
        self.__send(json.dumps({"command": "greet", "data": "Hello"}))


    def sayBye(self):
        self.__send(json.dumps({"command": "bye", "data": str(self.__uid)}))

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}))

    def close_all_sockets(self):
        self.close()
        for uid, process in self.__UserProcesses:
            process.terminate()
        print("All sockets closed")

    @property
    def uid(self):
        return self.__uid


class UserEnv(Client):
    def __init__(self, user_uid,key,pipe , serverAddress = "server", serverPort = 22346):
        super().__init__(serverAddress, serverPort, useSSL=False)
        self.running = True
        self.__uid = user_uid
        self.__key = key
        print("Key:", key)
        self.__cypher = Fernet(key.encode('utf-8'))
        self.__payload = None

        self.pingtime = None
        self.__auth_passed = False
        self.__pipe = pipe
        self.__remaining = 3
        self.tries = 0

        #self.startListener()

        self.authenticate()
        self.listen_loop()
        print("UserEnv started for user", self.__uid)


    def authenticate(self):
        print("Authenticating")
        self.__send(self.__uid)

    def __send(self, data : str):
        super().send(self.__encrypt(data))

    def __decrypt(self, data : bytes):
        return self.__cypher.decrypt(data)

    def __encrypt(self, data : str):
        return self.__cypher.encrypt(data.encode('utf-8'))

    def __receive(self, buffer_size=4096):
        data = b''
        while True:
            part = super().receive(buffer_size)
            data += part
            if len(part) < buffer_size:
                break
        return data

    def listen_loop(self):
        while self.running:
            try:
                data = self.__receive(4096)
            except BrokenPipeError:
                self.close()
                self.running = False
                break
            if data:
                self.__handleMessages(self.__decrypt(data).decode('utf-8'))
            else:
                pass

            if self.__payload is not None:
                self.runPayload()
                self.__payload = None
                self.__send(json.dumps({"command": "PayloadExecuted"}))
                self.__pipe.send_to_server(json.dumps({"Status": "PayloadExecuted", "uid": self.__uid}))
                self.close()
            else:
                self.tries += 1
                if self.tries > 500:
                    self.__tries = 0
                    self.__remaining -= 1
                    if self.__remaining < 0:
                        self.close()
                        self.running = False
                        break
                    else:
                        self.__send(json.dumps({"command": "Ready", "data": self.__uid}))
                time.sleep(0.01)

        print("Listener stopped")


    #def startListener(self):
    #    self.__listenerThread = Thread(target=self.__listener)
    #    self.__listenerThread.start()

    def __handleMessages(self, data : str):
        obj = json.loads(data)
        if obj['command'] == 'Auth_pass':
            print("Dataserver accepted Me !")
            self.__auth_passed = True
            # self.__send(self.__uid.encode('utf-8'))
            time.sleep(0.01)
            print("Sending ready message")
            self.__send(json.dumps({"command": "Ready", "data": self.__uid}))
        elif obj['command'] == 'OUT':
            self.running = False
            print("Client closed")
        elif obj['command'] == 'ping':
            self.__send(json.dumps({"command": "pong"}))
        elif obj['command'] == 'pong':
            try:
                self.pingtime = time.time() - self.pingtime
                print(f"Got pong from server in {self.pingtime} seconds")
            except TypeError:
                pass
        elif obj['command'] == 'Payload':
            self.__payload = obj['data']
            self.__send(json.dumps({"command": "PayloadReceived"}))
            print("Payload received : ", self.__payload)


    def __STDERR(self, data):
        self.__send(json.dumps({"command": "STDERR", "data": data}))

    def __STDOUT(self, data):
        self.__send(json.dumps({"command": "STDOUT", "data": data}))

    def runPayload(self):
        print("Running payload")
        runner = CompileRunner(self.__payload, self.__STDOUT, self.__STDERR)
        runner.run()

    def ping(self):
        self.pingtime = time.time()
        self.__send(json.dumps({"command": "ping"}))


    def close(self):
        self.__send(json.dumps({"command": "OUT"}))
        super().close()
        self.running = False
        print("UserEnv closed")

    @property
    def uid(self):
        return self.__uid

    @property
    def auth_passed(self):
        return self.__auth_passed

class CompileRunner:
    def __init__(self, code : str, stdout_callback, stderr_callback):
        self.__code = code

        self.__stdout_callback = stdout_callback
        self.__stderr_callback = stderr_callback
        self.__running = True
        self.__process = None
        self.__filename = None

    def detect_language(self, code):
        content = code
        if '#include' in content and 'stdio.h' in content:
            self.__filename = f"temp_code_{uuid.uuid4().hex}.c"
            return 'c'
        elif '#include' in content and 'iostream' in content:
            self.__filename = f"temp_code_{uuid.uuid4().hex}.cpp"
            return 'cpp'
        elif 'public class' in content :
            self.__filename = self.java_filename(content)
            return 'java'
        elif 'print(' in content or 'def' in content:
            self.__filename = f"temp_code_{uuid.uuid4().hex}.py"
            return 'python'
        else:
            self.__filename = f"temp_code_{uuid.uuid4().hex}.txt"
            return 'inconnu'

    def java_filename(self, code):
        # we must find the name of the public class
        code = code.split('\n')
        pubname = None
        for i in code:
            if 'public class' in i:
                pubname =  i.split(' ')[2].split('{')[0]
                break
        return pubname+'.java'



    def compile_C(self):
        with open(self.__filename, 'w') as f:
            f.write(self.__code)
        time.sleep(0.01)
        print("Compiling C code")
        output_file = 'a.out' if platform.system() != 'Windows' else 'a.exe'
        compile_cmd = ['gcc', self.__filename, '-o', output_file]
        self.__run_command(compile_cmd)

    def compile_CPP(self):
        with open(self.__filename, 'w') as f:
            f.write(self.__code)
        output_file = 'a.out' if platform.system() != 'Windows' else 'a.exe'
        compile_cmd = ['g++', self.__filename, '-o', output_file]
        self.__run_command(compile_cmd)

    def compile_Python(self):
        with open(self.__filename, 'w') as f:
            f.write(self.__code)

    def compile_Java(self):
        with open(self.__filename, 'w') as f:
            f.write(self.__code)
        compile_cmd = ['javac', self.__filename]
        self.__run_command(compile_cmd)

    def run_C(self):
        run_cmd = ['./a.out']
        self.__run_command(run_cmd)

    def run_CPP(self):
        run_cmd = ['./a.out']
        self.__run_command(run_cmd)

    def run_java(self):
        class_file = os.path.splitext(self.__filename)[0]
        run_cmd = ['java', class_file]
        self.__run_command(run_cmd)

    def run_python(self):
        python_name = None # we must try the command python3 first
        try :
            subprocess.run(['python3', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except :
            python_name = 'python'
        else :
            python_name = 'python3'



        run_cmd = [python_name, '-u', self.__filename]
        self.__run_command(run_cmd)

    def clean(self):
        os.remove(self.__filename)
        try :
            if platform.system() != 'Windows':
                os.remove('a.out')
            else:
                os.remove('a.exe')
        except FileNotFoundError:
            pass

    def run(self):
        lang = self.detect_language(self.__code)
        print(f"Detected language: {lang}")
        time.sleep(0.05)
        if lang == 'c':
            self.compile_C()
            self.run_C()
            time.sleep(0.01)
            self.clean()
            time.sleep(0.01)
        elif lang == 'cpp':
            self.compile_CPP()
            self.run_CPP()
            time.sleep(0.01)
            self.clean()
            time.sleep(0.01)
        elif lang == 'python':
            self.compile_Python()
            self.run_python()
            time.sleep(0.01)
            self.clean()
            time.sleep(0.01)
        elif lang == 'java':
            self.compile_Java()
            self.run_java()
            time.sleep(0.01)
            self.clean()
            time.sleep(0.01)

        self.exit()

    def __run_command(self, command):
        if command is str :
            pass
        else:
            command = ' '.join(command)
        for path in runner.run(command):
            self.__stdout_callback(path)
            # time.sleep(0.01) # to avoid overloading the client (lol)

    def exit(self):

        self.__running = False
        try:
            self.__process.kill()
        except AttributeError:
            pass


def main():
    client = ControlClient()

    # client.startListener()
    client.requestUid()
    try :
        client.loop()
    except KeyboardInterrupt:
        pass


    client.close_all_sockets()

if __name__ == "__main__":
    main()