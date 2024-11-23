The server start :
- a process is started for the user control connection
- a process is started for the node control connection
- a process is started for the data server


The user control connection process :
- listen for incoming connections
- accept incoming connections TODO: add authentication
- add User to the "UserBook"
- a new thread starts for the User

The node control connection process :
- listen for incoming connections
- accept incoming connections 
- add Node to the "NodeBook"
- a new thread starts for the Node

The data server process :
- start two listeners for incoming connections (Users and nodes) simmilar to the user control connection and node control connection but without ssl
- when a user comes in, it must be because he has a program to run
    User-Node association :
    - i receive from my superior (useruid,nodeuid, encryption key)
    - the user comes in and sends me his uid, i check if he is in my user-nodes list
    - the node will come in, and send me his uid, if he is in my user-nodes list, i will send that node object to the user object
    - the user will send me the program to run,without decrypting it i will send it to the node
    - the node will decrypt the program and run it
    - the node will send me the result, i will send it to the user



