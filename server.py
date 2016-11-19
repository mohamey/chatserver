import socket
import sys
import os
from _thread import interrupt_main
from multiprocessing import Pool, Manager
from time import time, sleep

IP_ADDRESS = '0.0.0.0'

joinId = 0

# Create a new chatroom
def createChatroom(name, IP, Port, chatrooms):
    chatrooms.append({})
    d = chatrooms[-1]
    d['Name'] = name
    d['ID'] = str(len(chatrooms))
    d['IP'] = IP
    d['Port'] = Port
    d['Members'] = []
    d['Messages'] = []
    chatrooms[-1] = d

# Given the name of a chatroom, check if it exists in list of existing rooms
def chatroomExists(name, chatrooms):
    for chatroom in chatrooms:
        if chatroom['Name'] == name:
            return True
    return False

# Given a list of rooms, get index of chatroom by name
def getRoomByName(chatrooms, name):
    index = 0
    for chatroom in chatrooms:
        if chatroom['Name'] == name:
            return index
        else:
            index += 1
    return -1

# Given list of chatrooms, get index of room by ID
def getRoomById(ID, chatrooms):
    index = 0
    for chatroom in chatrooms:
        if chatroom['ID'] == ID:
            return index
        else:
            index += 1
    return -1

# Given a list of members, return index of member by ID
def getMemberById(members, joinId):
    index = 0
    for member in members:
        if member['JoinId'] == joinId:
            return index
        else:
            index += 1

    return -1

# Listen for messages on a connection
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
def spawnRoom(sock, name, chatrooms):
    # Start listening for connections
    sock.listen(10)
    print("Room Listening on {}".format(sock.getsockname()))
    cindex = getRoomByName(chatrooms, name)
    if cindex == -1:
        print("Room {} could not be found".format(name))
        sys.exit()

    # Wait and listen for client connections
    while True:
        # Make a blocking call to wait for connections
        print("Room {} Listening for connections...".format(name))
        conn, addr = sock.accept()

        # Get message from connection
        data = listen(conn)
        message = data.decode('utf-8')

        conn.close()

        # Parse message
        message_lines = message.split('\n')
        details = []
        for line in message_lines:
            if line:
                detail = line.split(':')[1]
                details.append(detail.strip())

        # Parse message from client
        if message.startswith('CHAT'):
            cindex = getRoomByName(chatrooms, name)
            chatroom = chatrooms[cindex]

            # First make sure joinid matches user in the room
            clientIndex = getMemberById(chatroom['Members'], details[1])
            if clientIndex != -1:
                # Add Message object to list of messages for chat room
                message_object = {
                    'ID': len(chatroom['Messages']),
                    'User': details[2],
                    'Message': details[3]
                }
                chatroom['Messages'].append(message_object)
                cindex = getRoomByName(chatrooms, name)
                chatrooms[cindex] = chatroom

                # Create message object to send to members
                msg = "CHAT: {}\n".format(details[0])
                msg += "CLIENT_NAME: {}\n".format(details[2])
                msg += "MESSAGE: {}\n".format(details[3])
                msg_bytes = msg.encode()

                # Get up to date chatroom details
                cindex = getRoomByName(chatrooms, name)
                chatroom = chatrooms[cindex]
                # Send message to all chat room users
                for member in chatroom['Members']:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as memSock:
                        memSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        memSock.connect(('0.0.0.0', int(member['Port'])))
                        memSock.send(msg_bytes)

# If server is main thread, initialise it
if __name__ == '__main__':
    with Manager() as manager:
        # Chatrooms
        chatrooms = manager.list()

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

            # Start listening on socket
            sock.listen(15)
            print("Server listening on {}:{}".format(HOST, PORT))

            # Wait and listen for client connections
            while True:
                # Make a blocking call to wait for connections
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
                    if not chatroomExists(roomName, chatrooms):
                        chatSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        chatSocket.bind(('', 0))
                        chatPort = chatSocket.getsockname()[1]
                        print("Creating Chatroom {}".format(roomName))
                        createChatroom(roomName, IP_ADDRESS, chatPort, chatrooms)

                        # Assign the chat room to a worker thread
                        workers.apply_async(spawnRoom, [chatSocket, details[0], chatrooms])

                    # Add new member to list of chatroom members
                    roomIndex = getRoomByName(chatrooms, roomName)
                    chatroom = chatrooms[roomIndex]
                    member_object = {
                        'JoinId': str(joinId),
                        'Name': details[3],
                        'IP': addr[0],
                        'Port': addr[1]
                    }

                    chatroom['Members'].append(member_object)
                    chatrooms[roomIndex] = chatroom

                    # Send back response to client containing room details
                    response = 'JOINED_CHATROOM: {}\n'.format(roomName)
                    response += 'SERVER_IP: {}\n'.format(chatroom['IP'])
                    response += 'PORT: {}\n'.format(chatroom['Port'])
                    response += 'ROOM_REF: {}\n'.format(chatroom['ID'])
                    response += 'JOIN_ID: {}\n'.format(str(joinId))

                    conn.send(response.encode())
                    conn.close()

                    joinId += 1

                elif message.startswith('LEAVE_CHATROOM'):
                    print("Request to leave received")
                    response = ""
                    # Get chatroom from ID, remove client from member list
                    roomIndex = getRoomById(details[0], chatrooms)
                    if roomIndex != -1:
                        chatroom = chatrooms[roomIndex]
                        # Remove member by id
                        memberIndex = getMemberById(chatroom['Members'], details[1])
                        if memberIndex != -1:
                            del chatroom['Members'][memberIndex]
                            chatrooms[roomIndex] = chatroom

                            # Send back the response
                            response = "LEFT_CHATROOM: {}\n".format(details[0])
                            response += "JOIN_ID: {}\n".format(details[1])
                        else:
                            response = "ERROR_CODE: 404\nERROR_DESCRIPTION: Member {} not found\n".format(details[1])
                    else:
                        response = "ERROR_CODE: 404\nERROR_DESCRIPTION: Room {} not found".format(details[0])

                        conn.send(response.encode())
                        conn.close()
                elif message.startswith('DISCONNECT'):
                    print("Request to disconnect received")
                    # Remove client from all existing rooms
                    for i in range(0, len(chatrooms)):
                        temp = chatrooms[i]
                        for member in temp['Members']:
                            if member['Name'] == details[2]:
                                temp['Members'].remove(member)
                                break
                        chatrooms[i] = temp

                    conn.close()
