import socket
from time import sleep
from sys import argv, exit
from multiprocessing import Pool

rooms = []

# Get room by name
def getRoomByName(name):
    global rooms
    index = 0
    for room in rooms:
        if room['Name'] == name:
            return index
        else:
            index += 1
    return -1

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

def listenForServer(portNo):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSock:
        serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSock.bind(('0.0.0.0', portNo))
        serverSock.listen(10)
        while True:
            con, addr = serverSock.accept()
            data = listen(con)
            if data:
                print(data.decode('utf-8'))
            data = b''

def sendMessage(room, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        destination = (room['IP'], int(room['Port']))
        sock.connect(destination)
        roomId = room['ID']
        joinId = room['JoinId']
        name = room['Name']
        msg = "CHAT: {}\nJOIN_ID: {}\nCLIENT_NAME: {}\nMESSAGE: {}\n\n".format(roomId, joinId, name, message)
        msg_bytes = msg.encode()
        sock.send(msg_bytes)

def leaveRoom(room, destination):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect(destination)
        roomId = room['ID']
        joinId = room['JoinId']
        name = room['Name']
        msg = "LEAVE_CHATROOM: {}\nJOIN_ID: {}\nCLIENT_NAME: {}\n".format(roomId, joinId, name)
        msg_bytes = msg.encode()
        sock.send(msg_bytes)
        data = listen(sock)
        print(data.decode())

def joinRoom(destination, chatroom, name):
    global rooms
    global workers

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Open connection to server
    try:
        # Connect to the server
        sock.connect(destination)
    except socket.error as msg:
        print(str(msg[1]))
        exit()

    # Format message to send to server
    joinMessage = 'JOIN_CHATROOM: {}\nCLIENT_IP: 0\nPORT: 0\nCLIENT_NAME: {}\n'.format(chatroom, name)

    # Join chatroom
    sock.send(joinMessage.encode())

    # Listen for response
    data = listen(sock)

    # Print the result
    message = data.decode('utf-8')
    print(message)

    # Parse message
    message_lines = message.split('\n')
    details = []
    for line in message_lines:
        if line:
            detail = line.split(':')[1]
            details.append(detail)

    # If successful
    if message.startswith('JOINED_CHATROOM'):
        room = {
            'ID': details[3].strip(),
            'Name': details[0].strip(),
            'JoinId': details[4].strip(),
            'IP': details[1].strip(),
            'Port': details[2].strip()
        }
        rooms.append(room)

        # Hand off original socket to background thread
        # This will listen for messages from the server
        port = sock.getsockname()
        return port

if __name__ == '__main__':
    # Handle command line arguments and get variables
    workers = Pool(10)
    HOST = ''
    PORT = 8080

    chatroom = 'main'
    name = 'nick'

    # Check arguments for a port number
    if '-p' in argv:
        pos = argv.index('-p')
        PORT = int(argv[pos+1])

    # Check arguments for a host
    if '-h' in argv:
        pos = argv.index('-h')
        HOST = str(argv[pos+1])

    # Check arguments for a chatroom
    if '-r' in argv:
        pos = argv.index('-r')
        chatroom = str(argv[pos+1])

    # Check arguments for a name
    if '-n' in argv:
        pos = argv.index('-n')
        name = str(argv[pos+1])

    mainServer = (HOST, PORT)

    while True:
        user_command = input('Please enter a command:\n')
        cmd_parts = user_command.split(' ')

        if cmd_parts[0].lower() == "send":
            roomName = cmd_parts[1]
            roomIndex = getRoomByName(roomName)
            if roomIndex != -1:
                room = rooms[roomIndex]
                message = ' '.join(cmd_parts[1:])
                sendMessage(room, message)
        elif cmd_parts[0].lower() == "leave_chatroom":
            # Get room details
            roomIndex = getRoomByName(details[1])
            if room == -1:
                print("Room not found")
            else:
                leaveRoom(rooms[roomIndex], mainServer)
        elif cmd_parts[0].lower() == "join":
            port = joinRoom(mainServer, cmd_parts[1], name)
            workers.apply_async(listenForServer, [port])
