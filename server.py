import socket
import sys
import os
from _thread import interrupt_main
from multiprocessing import Pool
from time import time

IP_ADDRESS = '46.101.83.147'
# Chatrooms
chatrooms = [
    {
        'Name': 'main',
        'ID': 0,
        'IP': IP_ADDRESS,
        'Port': '808080',
        'Members': [],
        'Messages': []
    }
]

# Client List
clients = []

joinId = 0

def createChatroom(name, IP, Port):
    newRoom = {
        'Name': name,
        'ID': len(chatrooms),
        'IP': IP,
        'Port': Port,
        'Members': [],
        'Messages': []
    }
    chatrooms.append(newRoom)

def chatroomExists(name):
    for chatroom in chatrooms:
        if chatroom['Name'] == name:
            return True
    return False

# Get room by name
def getRoomByName(name):
    index = 0
    for chatroom in chatrooms:
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

# Handle the incoming messages from the client
def handleMessage(conn, addr, msg):
    msg = msg.strip()
    message_lines = msg.split('\n')
    message_action = message_lines[0].split(':')[0]
    print(message_action)
    if msg_parts[0] in validMessages:
        func = validMessages[msg_parts[0]]
        func(conn, addr, msg)
    else:
        response = 'message: {} not recognized'.format(msg)
        conn.sendall(response.encode())

        data = listen(conn)

        msg_string = data.decode('utf-8')
        handleMessage(conn, addr, msg_string)

    return

# Listen for message from client
def listen(conn, timeout=2):
    data = b''
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
            # print("Data received")
            # print(data.decode())

    return data

# Assign a new worker thread to a room
def spawnRoom(sock, name):
    print("Started chatroom {}".format(name))
    # Start listening for connections
    sock.listen(5)
    print("Listening on {}".format(sock.getsockname()))

    # Wait and listen for client connections
    while True:
        # Make a blocking call to wait for connections
        conn, addr = sock.accept()
        print('Connected with {}:{}'.format(addr[0], str(addr[1])))

        data = listen(conn)

        message = data.decode('utf-8')
        print('{}: {}'.format(name, message))
        conn.close()

        # Parse message
        message_lines = message.split('\n')
        details = []
        for line in message_lines:
            detail = line.split(':')[1]
            details.push[detail]


# If server is main thread, initialise it
if __name__ == '__main__':
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
        workers.apply_async(spawnRoom, [chatSocket, 'main'])

        # Start listening on socket
        sock.listen(15)
        print("Server listening on {}:{}".format(HOST, PORT))

        # Wait and listen for client connections
        while True:
            # Make a blocking call to wait for connections
            print("Listening")
            conn, addr = sock.accept()
            print('Connected with {}:{}'.format(addr[0], str(addr[1])))

            data = listen(conn)

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
                    createChatroom(roomName, IP_ADDRESS, chatPort)

                    # Assign the chat room to a worker thread
                    workers.apply_async(spawnRoom, [chatSocket, details[0]])

                # Send back response to client containing room details
                chatroom = chatrooms[getRoomByName(roomName)]
                response = 'JOINED_CHATROOM: {}\n'.format(roomName)
                response += 'SERVER_IP: {}\n'.format(chatroom['IP'])
                response += 'PORT: {}\n'.format(chatroom['Port'])
                response += 'ROOM_REF: {}\n'.format(chatroom['ID'])
                response += 'JOIN_ID: {}\n'.format(str(joinId))

                conn.send(response.encode())
                conn.close()

                # Add new member to list of chatroom members
                chatroom['Members'].append(str(joinId))

                # Add client to clients list
                client = {
                    'JoinId': str(joinId),
                    'Name': details[3],
                    'IP': client_ip,
                    'Port': client_port
                }
                clients.append(client)
                joinId += 1
                print("Updated client and room details")
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

