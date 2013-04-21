"""
   Command-line arguments like -t time, period of time, minute unit
                               -n number, maximum login number
                               -p port, Listening ports
"""
__author__ = 'ldd'

import socket
import SocketServer
import optparse
import time
import threading


mylock = threading.RLock()


class LoginAmount(object):
    """
     Count the number of log in.
     Data structure: data is a dictionary, ip as key, value is a list just as l
                     l[0] is a pointer, the index of last update value.
                     each item in l[1:] has 2 fields, time, number of this time
                     the length of l[:] is period, I cycle using them.
     example:
     period = 4 then data will be like:
     {'10.2.0.2': [3, ['110930', 4], ['110931', 5],['110932', 3], ['110933',4],
      '10.2.0.3': [4, ['110931', 4], ['110932', 5],['110933', 3], ['110934',4]}
    """
    def __init__(self, period, number):
        self.data = {}
        self.period = period
        self.number = number

    def add_login(self, ip, str_now):
        """
         Add log number of ip.
        """
        vector = self.data.get(ip)
        mylock.acquire()
        if vector is not None:
            front = vector[0]
            if vector[front][0] == str_now:
                vector[front][1] += 1
            else:
                front = vector[0] = vector[0] % self.period + 1
                vector[front][0] = str_now
                vector[front][1] = 1
        else:
            new_vector = [[0, 0] for i in range(self.period)]
            new_vector.insert(0, 1)
            new_vector[1] = [str_now, 1]
            self.data.update({ip: new_vector})
        mylock.release()

    def can_login(self, ip):
        """
        To determine whether this ip exceeds the limit number.
        :return: True or False
        """
        now = time.time()
        str_now = time.strftime('%d%H%M')
        self.add_login(ip, str_now)
        vector = self.data.get(ip)
        low = time.strftime('%d%H%M', time.localtime(now - self.period * 60))
        if vector is None:
            return False
        else:
            total = reduce(lambda x, y: x + (y[1] if y[0] > low else 0),
                            vector[1:], 0)
            return total < self.number


class LimitLoginHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global login_amount
        while True:
            try:
                dataReceived = self.request.recv(1024).strip()
                if not dataReceived:
                    break
                is_can = login_amount.can_login(dataReceived)
                self.request.send(str(is_can))
            except socket.timeout as err:
                self.request.close()
                break

    def setup(self):
        self.request.settimeout(60)

    def finish(self):
        self.request.close()


def option_parser(parser):
    parser.add_option("-t", "--time", dest="time",
                       help="period of time, minute unit")
    parser.add_option("-n", "--number", dest="number",
                      help="maximum login number in a period of time")
    parser.add_option("-p", "--port", dest="port",
                      help="Listening ports")


def main():
    parser = optparse.OptionParser()
    option_parser(parser)
    (options, args) = parser.parse_args()
    global login_amount
    login_amount = LoginAmount(int(options.time), int(options.number))
    host, port = '127.0.0.1', int(options.port)
    server = SocketServer.ThreadingTCPServer((host, port), LimitLoginHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()
