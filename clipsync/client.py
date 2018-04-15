import json
import socket
import time

from clipsync import clip

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GObject, Gtk
except Exception:
    pass

# Hardcoded constant to call command to pull clipboard from server.
PULL_CLIP = json.dumps({'cmd': 'PULL'}) + '\n'


def sync_clipboard(server_hostname, server_port, last_text):
    ''' Sync clipboard with server.

    Basic procedure for syncing is as follows:
    connect to server -> send current clipboard (if a change has occurred)
    -> get current clipboard from server.

    This ensures that the current clipboard item is always update to date.

    Args:
    server_hostname (str): The hostname of the server to connect to, e.g 'localhost'
    server_port (int): The port of the server to connect to, e.g 7071
    last_text (str): The last text synced to the clipboard.

    Returns:
    bool: Whether GTK main loop should reset timeout. '''
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    with socket.socket() as sock:
        sock.connect((server_hostname, server_port))
        wsock = sock.makefile(mode='w')
        rsock = sock.makefile()
        new_text = clipboard.wait_for_text()
        if new_text != last_text:
            # New clipboard contents, create a clip object and
            # push it to server.
            dt = time.time()
            clip_dict = clip.clip_as_dict(clip.Clip(dt, new_text))
            # Append PUSH command to tell server we want to add
            # this clip to the server clipboard.
            clip_dict['cmd'] = 'PUSH'
            # After those operations clip_dict looks like:
            # clip_dict = {'cmd': 'PUSH', 'dt': now, 'contents': contents}
            cmd_str = json.dumps(clip_dict) + '\n'
            wsock.write(cmd_str)
            wsock.close()
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
            # TODO: rewrite with logging daemon.
            print(response_json['err'])
            return True, last_text
        # No error has occurred .: a successful clipboard item has
        # been returned.
        updated_clip = clip.Clip(**response_json)
        clipboard.set_text(updated_clip.contents, -1)
        clipboard.store()
        rsock.close()
        return True, updated_clip.contents


def start_client(hostname, port):
    ''' Start a client instance connecting to `hostname`:`port` for
    pushing/pulling clips.

    Starts a Gtk main thread calling `Client.sync_clipboard` every 5 seconds.

    Args:
        hostname (str): The host name of the clipsync server instance (e.g 'localhost')
        port (int): The port to connect to (e.g 7071)
    '''
    last_text = None

    def sync_client():
        nonlocal last_text
        reset, last_text = sync_clipboard(hostname, port, last_text)
        return reset

    GObject.timeout_add(5000, sync_client)
    Gtk.main()
