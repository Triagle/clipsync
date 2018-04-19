import asyncio
import re

import click

from . import client, server


def parse_size(size):
    ''' Parse a data size in any format into pure bytes.

    Args:
        size (str): The data string to parse.

    Returns:
        int: The number of bytes that data string represents.

    Raises:
        click.BadParameter: If the passed string is in an invalid format.

    Examples:
        >>> parse_size('100kb')
        100000
        >>> parse_size('100kbv')
        Traceback (most recent call last):
            ...
        click.exceptions.BadParameter: 100kbv is an invalid string. Should be in the format N(mb|gb|kb|b|).'''
    match = re.match(
        r'(?P<magnitude>\d+)\s*(?P<unit>kb|mb|gb|b)?$',
        size,
        flags=re.IGNORECASE)
    if match is None:
        raise click.BadParameter(
            f'{size} is an invalid string. Should be in the format N(mb|gb|kb|b|).'
        )
    unit_mapping = {'gb': int(1e9), 'mb': int(1e6), 'kb': 1000, 'b': 1}
    match_dict = match.groupdict('')
    return int(
        match_dict['magnitude']) * unit_mapping[match_dict.get('unit').lower()
                                                or 'b']


@click.group()
def cli():
    '''Start clipsync client/server.

    \b
    Examples:
        clipsync server # Server started on localhost:7071.
        clipsync client # Connects to localhost:7071 and syncs clipboard.
    '''
    pass


@cli.command('server')
@click.option(
    '--host',
    default='localhost',
    metavar='HOST',
    help="Hostname to bind to, e.g '0.0.0.0'")
@click.option(
    '--port', metavar='PORT', default=7071, help="Port to bind to, e.g 7070")
@click.option(
    '--max-clipboard-size',
    metavar='SIZE',
    default=str(server.CLIPBOARD_DEFAULT_MAX),
    help="Maximum size of the clipboard, e.g '5mb' or '5gb'",
    callback=lambda ctx, p, value: parse_size(value))
def start_server(host, port, max_clipboard_size):
    ''' Start clipsync server.

    \b
    Examples:
        clipsync server # Server started on localhost:7071.
        clipsync server --host='0.0.0.0' # Server started on 0.0.0.0:7071, global server.
        clipsync server --port 7070 # Server started on localhost:7070.
        clipsync server --host='0.0.0.0' --port 7070 # Server started on 0.0.0.0:7070.
    '''
    clip_server = server.ClipSyncServer(clipboard_max=max_clipboard_size)
    loop = asyncio.get_event_loop()
    coroutine = asyncio.start_server(
        clip_server.handle, host=host, port=port, loop=loop)
    socket_server = loop.run_until_complete(coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    socket_server.close()
    loop.run_until_complete(socket_server.wait_closed())
    loop.close()


@cli.command('client')
@click.option(
    '--host',
    default='localhost',
    metavar='HOST',
    help="Hostname to connect to, e.g '192.168.2.1'")
@click.option(
    '--port',
    metavar='PORT',
    default=7071,
    help='Port to connect to, e.g 7070')
@click.option(
    '--max-clip-item-size',
    metavar='SIZE',
    default=str(client.DEFAULT_MAX_CLIPBOARD_ITEM_SIZE),
    help=
    "Maximum size of any item on the clipboard to push to the server, e.g '5mb' or '5gb'",
    callback=lambda ctx, p, value: parse_size(value))
def start_client(host, port, max_clip_item_size):
    ''' Start clipsync client.

    \b
    Examples:
        clipsync client # Connects to localhost:7071 and syncs clipboard.
        clipsync client --host='192.168.2.1' --port=7070 # Connects to 192.168.2.1:7070 and syncs clipboard.
    '''
    client.start_client(host, port, max_clip_item_size)


if __name__ == '__main__':
    cli()
