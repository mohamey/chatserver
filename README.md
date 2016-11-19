# Multithreaded Chat Server
## Yasir Mohamed - 13318246
This repository currently contains a working implementation of a multithreaded chat server with clients to communicate with said server. The implementation is as follows:

### Server Implementation
Currently the server supports the creation of new chat rooms, clients leaving chat rooms, clients sending messages and clients disconnecting.
When the server is started, it defaults to waiting for a client to join a chatroom. Each chatroom that is created is spawned on it's own thread with it's own IP and Port. This is where clients must send messages for other members of the chatroom to see it. This is how the server handles messages:
* Join Chatroom: Check if chatroom exists, if it doesn't then create it and spawn a new thread to manage it. Then insert client details to shared chatroom memory object, and respond to the client with the chatroom thread's details.
* Send Message: Client must send a message to the chatroom thread, where it will be relayed to all existing members of the chatroom
* Leave_chatroom: Sent to the main chat server, server first checks that the specified chatroom exists then that the client is a member of the room. If both checks pass, the client is removed from the room and a response sent back to the client.
* Disconnect: When the server receives this message the client scans all chatroom member lists for the specified client and removes all occurrences of the client. The client is then disconnected.

#### Usage:
```bash
python3 server.py -p $portNumber
```
Run this to start the server on the specified port number, by default on the local machine. The server uses the IP '0.0.0.0' by default, though this can be changed at the top of the file.

### Client Implementation
The client is basically just a script that takes user input, parses it and performs one of the four specified actions (join, send, leave, disconnect). Since a client needs to be able to join multiple chat rooms, the client must be constantly have a socket listening for each chatroom. The way this works is that when a request to join a chatroom is made, the client creates a socket, makes a connection to the main server, and sends a join request for the specified room. The server saves the details of the clients socket (IP, Port) and adds the client to the room. Since the saved client details is how the server will contact the client in future, the client spawns a new thread and binds a new socket to the port used to join the chatroom. This thread always listens for messages from the server.

#### Usage
To run the client, use the command:
```bash
python3 client.py -p $portNumber -h $hostIP/Name -n $userName
```

This will present you with a prompt to enter a command. The commands are as follows:
```
join $roomName
```
```
send $roomName $message
```
```
leave_chatroom $roomName
```
```
disconnect
```
By default, whenever the client receives a new message it automatically prints it to standard output.
