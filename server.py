#!/usr/bin/env python3
import socketserver
import socket
import time
def peeraddr(s):
    ip, port = s.getpeername()
    return socket.inet_pton(s.family, ip) + bytes([port>>8, port&255])
ls = []
class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        if self.request.family != socket.AF_INET:
            return
        raddr = peeraddr(self.request)
        i = len(ls)-255 if len(ls) > 255 else 0
        ls.append((raddr, time.time()))
        while ls[i][1] < ls[-1][1]-60:
            i += 1
        del ls[:i]
        for i in range(len(ls)-1):
            if ls[i][0] == raddr:
                del ls[i]
                break
        self.request.sendall(bytes([len(ls)]) + b''.join(x[0] for x in ls))
with socketserver.TCPServer(('', 8086), MyTCPHandler, bind_and_activate=False) as server:
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    server.serve_forever()
