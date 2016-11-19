import socket
import sys
import os
from _thread import interrupt_main
from multiprocessing import Pool, Manager
from time import time

IP_ADDRESS = '0.0.0.0'

# Shared variable manager
manager = Manager()

# Chatrooms
chatrooms = manager.list([
    {
        'Name': 'main',
        'ID': 0,
        'IP': IP_ADDRESS,
        'Port': '808080',
        'Members': [],
        'Messages': []
    }
])

# chatrooms = manager.list()

# Client List
clients = manager.list()

joinId = 0

def createChatroom(name, IP, Port, chatrooms):
    newRoom = {
        'Name': name,
        'ID': len(chatrooms),
        'IP': IP,
        'Port': Port,
        'Members': [],
        'Messages': []
    }
    chatrooms.append(newRoom)
    print('APPENDED ROOM')
    print(len(chatrooms))

def chatroomExists(name):
    for chatroom in chatrooms:
        if chatroom['Name'] == name:
            return True
    return False

# Get room by name
def getRoomByName(name):
    index = 0
    for chatroom in chatrooms:
        print('names:')
        print(chatroom['Name'])
        if chatroom['Name'] == name:
            return index
        else:
            index += 1
    return -1

def getRoomById(ID):
    index = 0
    for chatroom in chatrooms:
        if chatroom['ID'] == ID:
            return index
        else:
            index += 1
    return -1

def getClientByName(name):
    index = 0
    for client in clients:
        if client['Name'] == name:
            return index
        else:
            index += 1

    return index

def getClientsInRoom(joinIds):
    results = []
    for joinId in joinIds:
        for client in clients:
            if client['JoinId'] == joinId:
                results.append((client['IP'], client['Port']))
                break

    return results

# Listen for message from client
def listen(conn, timeout=2, blocking=False):
    data = b''
    if blocking:
        conn.setblocking(0)
    while True:
        new_data = b''
        try:
            new_data = conn.recv(1024)
        except:
            pass

        # If nothing is received, exit the loop
        if not new_data:
            break
        else:
            data += new_data

    return data

# Assign a new worker thread to a room
def spawnRoom(sock, name, chatrooms, clients):
    # Start listening for connections
    sock.listen(5)
    print("Room Listening on {}".format(sock.getsockname()))
    cindex = getRoomByName(name)
    if cindex == -1:
        print("Room {} could not be found".format(name))
        sys.exit()

    # Wait and listen for client connections
    while True:
        # Make a blocking call to wait for connections
        print("Room {} Listening for connection...".format(name))
        conn, addr = sock.accept()
        print('Room Connected with {}:{}'.format(addr[0], str(addr[1])))

        data = listen(conn)

        message = data.decode('utf-8')
        print(message)
        conn.close()

        # Parse message
        message_lines = message.split('\n')
        details = []
        for line in message_lines:
            if line:
                detail = line.split(':')[1]
                details.append(detail)

        if message.startswith('CHAT'):
            # Add Message object to list of messages for chat room
            message_object = {
                'ID': len(chatrooms[cindex]['Messages']),
                'User': details[2],
                'Message': details[3]
            }
            chatrooms[cindex]['Messages'].append(message_object)
            for key in chatrooms[cindex]:
                print("{}: {}".format(key, chatrooms[cindex][key]))

            # Gather IP and Ports of current room members
            currentMembers = getClientsInRoom(chatrooms[cindex]['Members'])
            print('CURRENT MEMBERS: {}'.format(str(len(currentMembers))))

            # Create message object to send to members
            msg = "CHAT: {}\n".format(details[0])
            msg += "CLIENT_NAME: {}\n".format(details[2])
            msg += "MESSAGE: {}\n".format(details[3])
            msg_bytes = msg.encode()

            # Send message to all chat room users
            for member in currentMembers:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as memSock:
                    print("Sending message to member")
                    memSock.bind(member)
                    memSock.send(msg_bytes)
                    print("Sent message to member")


# If server is main thread, initialise it
if __name__ == '__main__':
    # Placed shared variables in manager server
    workers = Pool(10)
    # Create the server socket
    HOST = '0.0.0.0'
    PORT = 8080
    if '-p' in sys.argv:
        pos = sys.argv.index('-p')
        PORT = int(sys.argv[pos+1])

    # Create a socket object to be used for the port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Bind socket to local host/port
        try:
            sock.bind((HOST, PORT))
        except socket.error as msg:
            print(str(msg[1]))
            sys.exit()

        # Create process for main chatroom
        chatSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chatSocket.bind(('0.0.0.0', 0))

        # Assign the chat room to a worker thread
        workers.apply_async(spawnRoom, [chatSocket, 'main', chatrooms, clients])

        # Start listening on socket
        sock.listen(15)
        print("Server listening on {}:{}".format(HOST, PORT))

        # Wait and listen for client connections
        while True:
            # Make a blocking call to wait for connections
            print("Listening")
            conn, addr = sock.accept()
            print('Connected with {}:{}'.format(addr[0], str(addr[1])))

            data = listen(conn, blocking=True)

            message = data.decode('utf-8')

            # Parse message
            message_lines = message.split('\n')

            details = []
            for line in message_lines:
                if line:
                    detail = line.split(':')[1]
                    details.append(detail.strip())

            if message.startswith('JOIN_CHATROOM'):
                client_ip = addr[0]
                client_port = addr[1]

                # Details = chatroom name, client ip, client port, client name
                # If chatroom doesn't exist, create it
                roomName = details[0].strip()
                if not chatroomExists(roomName):
                    chatSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    chatSocket.bind(('', 0))
                    chatPort = chatSocket.getsockname()[1]
                    print("Creating Chatroom {}".format(roomName))
                    createChatroom(roomName, IP_ADDRESS, chatPort, chatrooms)

                    # Assign the chat room to a worker thread
                    workers.apply_async(spawnRoom, [chatSocket, details[0], chatrooms, clients])

                # Add new member to list of chatroom members
                roomIndex = getRoomByName(roomName)
                chatroom = chatrooms[roomIndex]
                chatroom['Members'].append(str(joinId))

                # Add client to clients list
                client = {
                    'JoinId': str(joinId),
                    'Name': details[3],
                    'IP': addr[0],
                    'Port': addr[1]
                }
                clients.append(client)
                joinId += 1
                print("Server Updated client and room details")

                # Send back response to client containing room details
                response = 'JOINED_CHATROOM: {}\n'.format(roomName)
                response += 'SERVER_IP: {}\n'.format(chatroom['IP'])
                response += 'PORT: {}\n'.format(chatroom['Port'])
                response += 'ROOM_REF: {}\n'.format(chatroom['ID'])
                response += 'JOIN_ID: {}\n'.format(str(joinId))

                conn.send(response.encode())
                conn.close()

            elif message.startswith('LEAVE_CHATROOM'):
                print("Request to leave received")

                # Get chatroom from ID, remove client from member list
                chatrooms[getRoomById(details[0])]['Members'].remove(details[1])

                # Send back the response
                response = "LEFT_CHATROOM: {}\n".format(details[0])
                response += "JOIN_ID: {}\n".format(details[1])

                conn.send(response.encode())
                conn.close()

            elif message.startswith('DISCONNECT'):
                print("Request to disconnect received")
                index = getClientByName(details[2])
                if index != -1:
                    conn.close()
                    del clients[index]
                    print("Client deleted")
                else:
                    print("Client not found")

