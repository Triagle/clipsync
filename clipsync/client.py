import json
import socket
import time

import clip

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GObject, Gtk
except Exception:
    pass

PULL_CLIP = json.dumps({'cmd': 'PULL'}) + '\n'


class Client:
    def __init__(self, hostname, port):
        self.last_text = None
        self.server_hostname = hostname
        self.server_port = port

    def sync_clipboard(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        with socket.socket() as sock:
            sock.connect((self.server_hostname, self.server_port))
            wsock = sock.makefile(mode='w')
            rsock = sock.makefile()
            new_text = clipboard.wait_for_text()
            if new_text != self.last_text:
                self.last_text = new_text
                dt = time.time()
                clip_dict = clip.clip_as_dict(clip.Clip(dt, self.last_text))
                clip_dict['cmd'] = 'PUSH'
                cmd_str = json.dumps(clip_dict) + '\n'
                wsock.write(cmd_str)
                wsock.close()
            else:
                wsock.write(PULL_CLIP)
                wsock.close()
            response_json = json.loads(rsock.readline())
            if 'err' in response_json:
                print(response_json['err'])
                return True
            updated_clip = clip.Clip(**response_json)
            clipboard.set_text(updated_clip.contents, -1)
            rsock.close()
        return True


def start_client(hostname, port):
    client = Client(hostname, port)
    GObject.timeout_add(5000, client.sync_clipboard)
    Gtk.main()
