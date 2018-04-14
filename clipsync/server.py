import json
import socketserver

import clip
from sortedcontainers import SortedList


def clip_as_str(clip_obj):
    return json.dumps(clip.clip_as_dict(clip_obj)) + '\n'


class ClipSyncServer(socketserver.TCPServer):
    def __init__(self, host_port, request_handler):
        super().__init__(host_port, request_handler)
        self.clipboard = SortedList(key=lambda c: c.dt)


class ClipSyncTCP(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def pull_clip(self, data):
        try:
            return clip_as_str(self.server.clipboard[-1])
        except IndexError:
            return json.dumps({'err': 'clipboard empty'}) + '\n'

    def push_clip(self, data):
        new_clip = clip.Clip(dt=int(data['dt']), contents=data['contents'])
        self.server.clipboard.add(new_clip)
        return self.pull_clip(data)

    def pop_clip(self, data):
        try:
            return clip_as_str(self.server.clipboard.pop())
        except IndexError:
            return json.dumps({'err': 'clipboard empty'}) + '\n'

    def handle(self):
        command_dispatch = {
            'PULL': self.pull_clip,
            'PUSH': self.push_clip,
            'POP': self.pop_clip
        }
        data = self.rfile.readline().strip()
        json_data = {}
        response = None
        try:
            json_data = json.loads(data)
        except json.JSONDecodeError:
            response = json.dumps({'err': f'{data} is not valid json.'}) + "\n"
        if 'cmd' not in json_data and response is None:
            response = json.dumps({
                'err':
                f'Must specific command in json request.'
            }) + '\n'
        elif response is None:
            response = command_dispatch[json_data['cmd']](json_data)
        self.wfile.write(response.encode())
