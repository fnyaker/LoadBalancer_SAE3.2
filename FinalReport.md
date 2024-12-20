# Global Architecture
## Master Server
- Acts like a proxy between clients and nodes (slaves)
- Does not run any code, only forwards requests to nodes
- Handles all the load balancing tasks

### Control server
- Secured with ssl
- Handles the "management" requests of the nodes and clients

### Data server
- Forward data between nodes and users
- Not secured with ssl but data is encrypted before sending by client or node

## Node (Slave)
- Runs the actual code of the client
- Can handle multiple clients at the same time

## Client (gui)
- First, connects to the master server
- Asks for a node and , when the master gives a node, connects to the data server, sends the code to the node, and print the result

# Choices
I had to choose solutions to implement the different parts of the project, here are the choices I made and why I made them

## Communication
I have chosen to have two connections for high speed even with a lot of nodes and clients.  
I chose ssl to secure the control connection because it provides good security.

## High load handling
My master server fork a new process for each new data connection, this way it exploits the full potential of the server, it can handle a lot of connections at the same time.

## Data transfer
I chose to use mainly json to transfer data because if offers a safe way to transfer data between the different parts of the project.

Internally (in the master server) i used multiprocessing queues to transfer data between processes without interfering with sockets and without compromising the security of the project.

# Difficulties
### Lack of time
Most of the time i spent is at home during my "free" time (which was no more free), and i had until 31/12/2024 to finish the project.     
To overcome that, i had to not focus on learning why there is a bug but on how to not make it crash the whole process.
Because of the lack of time, i had not time to learn how every lib work, plus, i had not time to extensively test the project, but, most of the bugs are fixed.

### SSL
I had to learn how to implement ssl and how it work, i've seen that two ssl conns on the same process is not possible
or at least, it is very complex to have something stable.

### Os compatibility
I had to code some function to make it work on most of the linux distros, the best example is python executable name, sometimes it is python3, sometimes python.

# Potential improvements
### Load balancing
I should have implemented a better load balancing algorythm that anticipates thje load that a client can put on a node.
### Security
Instead of running the code on the node, i should have run it on a docker container, this way, the node is not compromised if the code is malicious.
### Multiles files
Currently, i can only send a single file to run, i should have implemented a way to send an entire project to run.
### STDIN
Because of the lack of time, i had to forget about adding a stdin canal from the user client to the node, this way, the user could have interacted with the code running on the node.

# Conclusion
It was a interresting project, with a lot of challenge and possibilities, but, because of the lack of time, i had to make some choices that i would not have made if i had more time.
