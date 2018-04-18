import json
import socketserver

from sortedcontainers import SortedList

from . import clip


def clip_as_str(clip_obj):
    ''' Convert a clipboard object to a JSON formatted string (plus newline).

    Args:
        clip_obj (Clip): Clip object to convert to string.

    Returns:
        str: A JSON object represented as a string plus a newline.

    Examples:
        >>> clip = Clip(dt=1, contents='clipboard example')
        >>> clip_as_str(clip)
        '{"dt": 1, "contents": "clipboard example"}\n'
    '''
    return json.dumps(clip_obj, default=clip.json_encode) + '\n'


class ClipSyncServer(socketserver.TCPServer):
    ''' ClipSyncServer object holds global server data, i.e the clipboard.
    See socketserver.TCPServer for more details.

    Attributes:
        clipboard (:obj:`SortedList` of :obj:`Clip`): A clipboard list sorted by clip datetime.
    '''

    def __init__(self, host_port, request_handler):
        super().__init__(host_port, request_handler)
        self.clipboard = SortedList()


class ClipSyncTCP(socketserver.StreamRequestHandler):
    ''' Simple stream based clipboard request handler.
    The `ClipSyncTCP.handle` method actually handles TCP requests, see
    that method for documentation on request handling.
    For more information on request handlers see `socketserver.StreamRequestHandler`.
    '''

    def pull_clip(self, data):
        ''' Pull the latest clip from the sorted clipboard.
        Args:
            data (dict): JSON request data. Ignored.
        Returns:
            dict: JSON representing either clip on success, or a JSON error object, to be passed to client
        '''
        try:
            return clip_as_str(self.server.clipboard[-1])
        except IndexError:
            return json.dumps({'err': 'clipboard empty'}) + '\n'

    def push_clip(self, data):
        ''' Push a clip onto sorted clipboard.
        Args:
            data (list of dict): A list of JSON clip objects, encoded as per `clip.encode_clip`
        Returns:
            dict: The top clip on the clipboard (see `ClipSyncTCP.pull_clip`) for details.
        '''
        for clip_data in data:
            new_clip = clip.Clip(
                dt=int(clip_data['dt']), contents=clip_data['contents'])
            self.server.clipboard.add(new_clip)
        return self.pull_clip(data)

    def pop_clip(self, data):
        ''' Pop the latest clip from the sorted clipboard. Modifies clipboard.
        Args:
            data (dict): JSON request data. Ignored.
        Returns:
            dict: JSON representing either clip on success, or a JSON
            error object, to be passed to client.
        '''
        try:
            return clip_as_str(self.server.clipboard.pop())
        except IndexError:
            return json.dumps({'err': 'clipboard empty'}) + '\n'

    def handle(self):
        ''' Handle a new TCP request.
        Requests are json objects that follow a simple structure::

            {
                'cmd': cmd, # PULL|PUSH|POP
                'data': data # Clipboard items, ...
            }

        The `data` field is omitted for POP/PULL requests.
        Responses are either a JSON error object or the successful
        response from the appropriate method.

        JSON error object:

            {
                'err': msg
            }

        Successful responses will not have the `err` keyword in them.

        The appropriate method call is decided by a command dispatch,
        a dictionary mapping the value of the `cmd` field to a method
        call.
        '''
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
                f'Must specify command in json request.'
            }) + '\n'
        elif response is None:
            response = command_dispatch[json_data['cmd']](json_data.get(
                'data', None))
        self.wfile.write(response.encode())
