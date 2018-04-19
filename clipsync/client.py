import json
import logging
import socket
import time

from . import clip

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GObject, Gtk
except Exception:
    pass

DEFAULT_MAX_CLIPBOARD_ITEM_SIZE = int(1e6)

# Hardcoded constant to call command to pull clipboard from server.
PULL_CLIP = json.dumps({'cmd': 'PULL'}) + '\n'


class Client:
    ''' The Client object encapsulates state regarding clipboard syncing.

    The Client builds a buffer that it sends to the server
    regularly. Buffer modification happens the moment the clipboard
    changes. '''

    def __init__(self,
                 hostname,
                 port,
                 max_clipboard_item_size=DEFAULT_MAX_CLIPBOARD_ITEM_SIZE):
        ''' Create a new Client instance.

        Args:
            hostname (str): The hostname to connect to, e.g 'localhost'
            port (int): The port to connect to, e.g 7071
            max_clipboard_item_size (int): The maximum size (in bytes) that any clipboard item can be. '''
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clip_buffer = []
        self.max_clipboard_item_size = max_clipboard_item_size
        self.server_hostname = hostname
        self.server_port = port
        self._self_set = False
        self.last_clipboard_change = time.time()

    def run(self):
        ''' Start an instance of the Client. '''
        self.clipboard.connect('owner-change', self.push_clip_item)
        GObject.timeout_add(5000, self.sync_clipboard)
        Gtk.main()

    def push_clip_item(self, clipboard, event):
        ''' Push a clipboard item to the clipboard buffer.

        Note:
            This method is intended to be bound to the `owner-change` signal from `Gtk.Clipboard`

        Args:
            clipboard (Gtk.Clipboard): The emitter of the clipboard event (self.clipboard).
            event (Gdk.EventOwnerChange): Information about the event (event time etc). '''
        # Two cases, one the clipboard was updated by the client, and
        # another when it was updated by some external application.
        new_text = self.clipboard.wait_for_text()
        self.last_clipboard_change = event.time
        new_clip = clip.Clip(event.time, new_text)

        if self._self_set is False and new_clip.size < self.max_clipboard_item_size:
            # Clipboard was updated by external application. Push to
            # clipboard buffer.
            self.clip_buffer.append(new_clip)
        else:
            # Clipboard was updated by the client, unset this flag to
            # allow the next event (maybe not by client) to be handled
            # properly.
            self._self_set = False

    def sync_clipboard(self):
        ''' Sync clipboard with server.

        Basic procedure for syncing is as follows:
        connect to server -> send current clipboard (if a change has occurred)
        -> get current clipboard from server.

        This ensures that the current clipboard item is always update to date.

        Note:
            This method should be bound to a timeout via `GObject.timeout_add`.

        Returns:
               bool: Whether or not to renew the GObject timer, True to renew, False otherwise. '''
        logging.basicConfig()
        logger = logging.getLogger('clipsync')
        with socket.socket() as sock:
            sock.connect((self.server_hostname, self.server_port))
            wsock = sock.makefile(mode='w')
            rsock = sock.makefile()
            if len(self.clip_buffer) > 0:
                # New clipboard contents, create a command and
                # push it to server.
                command = {'cmd': 'PUSH', 'data': self.clip_buffer}
                cmd_str = json.dumps(command, default=clip.json_encode) + '\n'
                wsock.write(cmd_str)
                wsock.close()
                self.clip_buffer.clear()
                # No need to PULL here as the PUSH command returns the
                # top clipboard item after pushing.
            else:
                # No clipboard contents, but other devices may have
                # changed so pull to update.
                wsock.write(PULL_CLIP)
                wsock.close()
            response_json = json.loads(rsock.readline())
            if 'err' in response_json:
                # An error has occured, print and reset timeout.
                logger.error(response_json['err'])
                return True
            # No error has occurred .: a successful clipboard item has
            # been returned.
            updated_clip = clip.Clip(**response_json)
            # Because the server does not necessarily have a
            # *complete* history of the clipboard (especially if
            # certain clippings have been exempted for being too
            # large), we only update if the server has a newer clip than
            # the last clipboard change.
            if updated_clip.dt > self.last_clipboard_change:
                # Let self.push_clip_item know that the clipboard has
                # been updated by the program.
                self._self_set = True
                self.clipboard.set_text(updated_clip.contents, -1)
                self.clipboard.store()
            rsock.close()
        return True


def start_client(hostname, port, max_clip_item_size):
    ''' Start a client instance connecting to `hostname`:`port` for
    pushing/pulling clips.

    Starts a Gtk main thread calling `Client.sync_clipboard` every 5 seconds.

    Args:
        hostname (str): The host name of the clipsync server instance (e.g 'localhost')
        port (int): The port to connect to (e.g 7071)
    '''
    client = Client(hostname, port, max_clip_item_size)
    client.run()
