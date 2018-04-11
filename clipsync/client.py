import json
import socket
import time

import gi
from gi.repository import Gdk, Gtk

import clip

PULL_CLIP = json.dumps({'cmd': 'PULL'}) + '\n'


def start_client():
    last_text = None
    while True:
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        with socket.socket() as sock:
            sock.connect(('localhost', 7071))
            wsock = sock.makefile(mode='w')
            rsock = sock.makefile()
            print('waiting on new text...')
            new_text = clipboard.wait_for_text()
            print(last_text, new_text)
            if new_text != last_text:
                last_text = new_text
                dt = time.time()
                clip_dict = clip.clip_as_dict(clip.Clip(dt, last_text))
                clip_dict['cmd'] = 'PUSH'
                cmd_str = json.dumps(clip_dict) + '\n'
                print(f'sending: {repr(cmd_str)}')
                wsock.write(cmd_str)
                wsock.close()
            else:
                wsock.write(PULL_CLIP)
                wsock.close()
            print('reading from client...')
            updated_clip = clip.Clip(**json.loads(rsock.readline()))
            print(f'read from client: {updated_clip}')
            print(f'Setting clipboard text to: {updated_clip.contents}')
            clipboard.set_text(updated_clip.contents, -1)
            rsock.close()
        time.sleep(1)


start_client()
