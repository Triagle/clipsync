import json

from sortedcontainers import SortedList

from . import clip

# Maximum size of clipboard list in bytes, default 5 megabytes
CLIPBOARD_DEFAULT_MAX = 5000000


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


class ClipSyncServer:
    ''' ClipSyncServer object holds global server data, i.e the clipboard.
    See socketserver.TCPServer for more details.

    Attributes:
        clipboard (:obj:`SortedList` of :obj:`Clip`): A clipboard list sorted by clip datetime.
        clipboard_max (int): The maximum size of the clipboard in memory (as bytes).
        clipboard_current (int): The current size of the clipboard in memory (as bytes).
    '''

    def __init__(self, clipboard_max=CLIPBOARD_DEFAULT_MAX):
        ''' Initialize a new clip sync server.

        Args:
            clipboard_max (int, optional): The maximum clipboard size in memory (as bytes). '''
        self.clipboard = SortedList()
        self.clipboard_max = clipboard_max
        self.clipboard_current = 0

    def trim_clipboard(self):
        ''' Trims clipboard until the size of the clipboard history is
        less than the maximum size allowed. '''
        while self.clipboard_current > self.clipboard_max and len(
                self.clipboard) > 0:
            item = self.clipboard.pop(0)
            self.clipboard_current -= item.size

    def pull_clip(self, data):
        ''' Pull the latest clip from the sorted clipboard.
        Args:
            data (dict): JSON request data. Ignored.
        Returns:
            dict: JSON representing either clip on success, or a JSON error object, to be passed to client
        '''
        try:
            return clip_as_str(self.clipboard[-1])
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
            self.clipboard.add(new_clip)
            self.clipboard_current += new_clip.size
        self.trim_clipboard()
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
            return clip_as_str(self.clipboard.pop())
        except IndexError:
            return json.dumps({'err': 'clipboard empty'}) + '\n'

    async def handle(self, rfile, wfile):
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

        Args:
            rfile (asyncio.StreamReader): A stream to read client data from.
            wfile (asyncio.StreamWriter): A stream to write data to
                                          the client asynchronously.
        '''
        command_dispatch = {
            'PULL': self.pull_clip,
            'PUSH': self.push_clip,
            'POP': self.pop_clip
        }
        data = await rfile.readline()
        data = data.strip()
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
        wfile.write(response.encode())
        await wfile.drain()
        wfile.close()
