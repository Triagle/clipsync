import click

from . import client, server


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
def start_server(host, port):
    ''' Start clipsync server.

    \b
    Examples:
        clipsync server # Server started on localhost:7071.
        clipsync server --host='0.0.0.0' # Server started on 0.0.0.0:7071, global server.
        clipsync server --port 7070 # Server started on localhost:7070.
        clipsync server --host='0.0.0.0' --port 7070 # Server started on 0.0.0.0:7070.
    '''
    with server.ClipSyncServer((host, port), server.ClipSyncTCP) as server_cls:
        server_cls.serve_forever()


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
def start_client(host, port):
    ''' Start clipsync client.

    \b
    Examples:
        clipsync client # Connects to localhost:7071 and syncs clipboard.
        clipsync client --host='192.168.2.1' --port=7070 # Connects to 192.168.2.1:7070 and syncs clipboard.
    '''
    client.start_client(host, port)


if __name__ == '__main__':
    cli()
