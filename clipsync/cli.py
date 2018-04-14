import click

import client
import server


@click.group()
def cli():
    pass


@cli.command('server')
@click.option('--host', default='localhost')
@click.option('--port', default=7071)
def start_server(host, port):
    ''' Start clipsync server. '''
    with server.ClipSyncServer((host, port), server.ClipSyncTCP) as server_cls:
        server_cls.serve_forever()


@cli.command('client')
@click.option('--host', default='localhost')
@click.option('--port', default=7071)
def start_client(host, port):
    ''' Start clipsync client. '''
    client.start_client(host, port)


if __name__ == '__main__':
    cli()
