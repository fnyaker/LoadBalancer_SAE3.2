# Install

# Required packages

- `python3` (`python` in some linux distros) and its base libs)

- `cryptography` python lib, it is included by default on most of the python installations

- for the nodes :

    - `psutil` python lib

    - `gcc` if you want the node to be able to run c code

    - `g++` for c++

    - `javac` for running java code (`openjdk-17-jdk-headless` on debian 12)

- for the master server :

    - nothing too special except a decent network link if you want many users

- for the client :

    - `pyqt6`

# Installation process

### Requirements

- a machine running linux (others should work) with `openssl` installed and in the path :

    - open a terminal

    - type `openssl` , if you get an error, openssl is not correctly installed on your system

    - to install openssl on debian based systems run `apt install openssl` as root

    - to install openssl on fedora based distros, run `dnf install openssl` as root

    - to install openssl on arch based distros, run `pacman -S openssl` as root

### Step-by-step

1. Clone the repo

2. run `generate_packages.py` from a terminal opened in the project root (where that script is located)

    1. you will be asked for many info, this is for the certificates generations, most of the info is "just" for better security of the cert but THE MOST IMPORTANT info is when asked for `Common Name (eg, your name or your server's hostname)` , you will have to put :

        1. the first time, the domain name that the users will use to access the server (if you only test on a single machine, put localhost)

        2. the 2nd time, the domain name the nodes will be using to access your server

3. A new folder `Packages` has been created, open it

    1. Here you got 3 independent "programs"

4. To run, execute `Main.py` but, before that, you should configure the servers (node and master) to make them run correctly





# Configuration

All configuration happens in `config.py`, if there is not `config.py`, there is no need for it.

## Master

There are two classes, Users and Nodes

### Users

```python
listener_address = "0.0.0.0" # where the server is gonna listen for incoming users
external_address = "server" # the hostname users will have to type to connect to your server (the one in the ssl cert)
listener_port = 12345 # where the server is gonna listen for incoming users
external_port = 12345 # the port the user put in its client app to connect

dataserver_listener_address = "0.0.0.0" # where the dataserver (higher bandwith) is gonna listen for users
dataserver_external_address = "server" # what the user client will connect to when opening a data session
dataserver_listener_port = 22345 # where the dataserver will listen to users
dataserver_external_port = 22345 # the port the user client app will try to reach
```

note that external data server info is gonna be transmitted to the client by the master automatically when needed



### Nodes

```python
listener_address = "0.0.0.0"
external_address = "server"
listener_port = 12346
external_port = 12346

dataserver_listener_address = "0.0.0.0"
dataserver_external_address = "server"
dataserver_listener_port = 22346
dataserver_external_port = 22346
```

Same as for Users but for the nodes

## Node

```python
max_processes = 1 # Maximum number of user/processes per node before we use another node
absolute_max_processes = 3 # Maximum number of user/processes per node before we refuse to add more users

master_address = "server" # Address of the master control server (external_address in the node class)
master_port = 12346 # Port of the master control server
```

## User client

You will be asked for the external server address(domain name) and port.



