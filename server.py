import socket
import sys
import os
from _thread import interrupt_main
from multiprocessing import Pool
from time import time

IP_ADDRESS = '46.101.83.147'
# Chatrooms
chatrooms = {
    1: {
        'name': 'main',
        'IP': IP_ADDRESS,
        'PORT': '808080',
        'members': []
    }
}

# Client List
clients = []

# Known message formats
validMessages = {
    ''
}

# Handle the incoming messages from the client
def handleMessage(conn, addr, msg):
    msg = msg.strip()
    message_lines = msg.split('\n')
    message_action = msg.split(':')[0]
    print(message_action[0])
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
    begin = time()
    while True:
        # if data and time() - begin > timeout:
        #     break

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
            print("Data received")
            print(data.decode())

    return data

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

        # Start listening on socket
        sock.listen(15)
        print("Server listening on {}:{}".format(HOST, PORT))

        # Wait and listen for client connections
        while True:
            # Make a blocking call to wait for connections
            conn, addr = sock.accept()
            print('Connected with {}:{}'.format(addr[0], str(addr[1])))

            data = listen(conn)
            conn.send('done'.encode())
            conn.close()

            msg_string = data.decode('utf-8')
            print("LeString: {}".format(msg_string))

            workers.apply_async(handleMessage, [conn, addr, msg_string])

    print("Closing Server")
