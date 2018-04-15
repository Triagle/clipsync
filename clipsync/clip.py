from collections import namedtuple

Clip = namedtuple('Clip', ['dt', 'contents'])


def clip_as_dict(clip):
    ''' Return clip object as a dictionary. Used for conversion to a
    JSON string.

    Args:
       clip: (Clip): Clip object to convert to dictionary

    Returns:
       dict: A dictionary containing the datetime and contents of the clip

    Examples:
       >>> clip = Clip(dt=1523769986, contents='testing the clipboard')
       >>> clip_as_dict(clip)
       {'dt': 1523769986, 'contents': 'testing the clipboard'} '''
    return {'dt': clip.dt, 'contents': clip.contents}
