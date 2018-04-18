from functools import singledispatch, total_ordering


@total_ordering
class Clip:
    ''' This object represents a single clipboard item.

    Clipboard items consist of the time the clipboard item was copied,
    and the contents of the copied text.

    Attributes:
        dt (int): The datetime (seconds since epoch) of the clipboard
                  item.
        contents (string): The contents of the clipboard item.
    '''

    def __init__(self, dt, contents):
        ''' Create a new clipboard object.

        Args:
            dt (int): The datetime (seconds since epoch) of the
                      clipboard item.
            contents (string): The contents of the clipboard item. '''
        self.dt = dt
        self.contents = contents

    @property
    def size(self):
        ''' Return the length of the clipboard contents in bytes.

        Returns:
            int: The size of the clipboard in bytes.

        Examples:
            >>> clip = Clip(dt=1523769986, contents='testing the clūpboard')
            >>> len(clip.contents)
            21
            >>> clip.size
            22 '''
        return len(self.contents.encode())

    def __le__(self, other):
        return self.dt < other.dt

    def __eq__(self, other):
        return self.dt == other.dt

    def __repr__(self):
        name = self.__class__.__name__
        return f'{name}(dt={self.dt}, contents={repr(self.contents)})'


@singledispatch
def json_encode(val):
    ''' Encode a json value, with extra hooks to encode Clip.

    Note:
        This value should be provided as the default argument to
        json.dump(s).

    Args:
        val (object): The value to encode.

    Returns:
        json_val: The object expressed in JSON primitives (dict, list,
                  int, str, ...).

    Example:
        >>> json_encode(3)
        3
        >>> clip = Clip(dt=1523769986, contents='testing the clipboard')
        >>> json_encode(clip)
        {'dt': 1523769986, 'contents': 'testing the clipboard'} '''
    return val


@json_encode.register(Clip)
def encode_clip(clip):
    ''' Return clip object as a dictionary. Used for conversion to a
    JSON string.

    Args:
        clip: (Clip): Clip object to convert to dictionary

    Returns:
        dict: A dictionary containing the datetime and contents of the clip

    Examples:
       >>> clip = Clip(dt=1523769986, contents='testing the clipboard')
       >>> encode_clip(clip)
       {'dt': 1523769986, 'contents': 'testing the clipboard'} '''
    return {'dt': clip.dt, 'contents': clip.contents}
