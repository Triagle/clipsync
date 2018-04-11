from collections import namedtuple

Clip = namedtuple('Clip', ['dt', 'contents'])


def clip_as_dict(clip):
    return {'dt': clip.dt, 'contents': clip.contents}
