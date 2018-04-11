import socketserver

import server

HOST, PORT = 'localhost', 7071

with server.ClipSyncServer((HOST, PORT), server.ClipSyncTCP) as server:
    server.serve_forever()
