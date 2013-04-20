__author__ = 'ldd'

import socket


def main():
    host = '127.0.0.1'
    port = 50081
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    while True:
        data = raw_input()
        if not data or data == 'exit':
            break
        client.send('%s\r\n' % data)
        data = client.recv(1024)
        if not data:
            break
        print data.strip()

if __name__ == '__main__':
    main()
