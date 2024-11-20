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
- when a user comes in, he will get associated with a node 
- if a node get disconnected, the user will be associated with another node
    User-Node association :
    - User connects
    - Data server asks his superior wich node should be associated with the user
    - Node is asked to open a new session (connection to the Data server) for that user with the user's encryption key via the node control connection
    - Node opens a new connection and gets authenticated with its uid and user's encryption key
    - That node object is then given to the user object and they are associated

