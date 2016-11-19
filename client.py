import socket
from time import sleep
from sys import argv, exit
from multiprocessing import Pool

rooms = []

def listen(conn, timeout=2):
    # Initialise variables for receiving data
    data = b''

    # Loop until no more data is received
    while True:
        new_data = sock.recv(1024)

        # Exit loop if nothing is received
        if not new_data: break

        data += new_data

    return data

def listenForServer(sock):
    while True:
        data = listen(sock)
        if data:
            print(data.decode())

if __name__ == '__main__':
    # Handle command line arguments and get variables
    HOST = ''
    PORT = 8080
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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

    # Open connection to server
    try:
        # Connect to the server
        sock.connect((HOST, PORT))
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
        workers = Pool(1)
        workers.apply_async(listenForServer, [sock])

        # Command line prompt to communicate with server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as comSock:
            print(room['IP'])
            print(room['Port'])
            sleep(2)
            comSock.connect((room['IP'], int(room['Port'])))
            msgString = "CHAT: {}\n".format(room['ID'])
            msgString += "JOIN_ID: {}\n".format(room['JoinId'])
            msgString += "CLIENT_NAME: {}\n".format(name)
            msgString += "MESSAGE: Testing\n\n"
            # print(msgString)
            comSock.send(msgString.encode())
