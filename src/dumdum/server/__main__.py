"""Host a dumdum server.

To use TLS encryption, you must provide a certificate and private key.
This can be specified as either:
1. A single file containing both the private key and certificate:
     --cert hello.pem
2. A pair of certificate and private key files, separated with a colon:
     --cert hello.crt:hello.key

"""

import argparse
import asyncio
import ssl

from dumdum.protocol import Channel
from dumdum.logging import configure_logging

from .manager import Manager
from .state import ServerState


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity",
    )
    parser.add_argument(
        "-c",
        "--channels",
        action="extend",
        nargs="+",
        help="A list of channels",
        type=parse_channel,
    )
    parser.add_argument(
        "--host",
        default=None,
        help="The address to host on",
    )
    parser.add_argument(
        "--port",
        default=6667,
        help="The port number to host on",
    )
    parser.add_argument(
        "--cert",
        default="",
        help="The SSL certificate and private key to use",
        type=parse_cert,
    )

    args = parser.parse_args()
    verbose: int = args.verbose
    channels: list[Channel] = args.channels or get_default_channels()
    host: str | None = args.host
    port: int = args.port
    ssl: ssl.SSLContext | None = args.cert

    configure_logging(verbose)

    state = ServerState()
    for channel in channels:
        state.add_channel(channel)

    try:
        asyncio.run(host_server(state, host, port, ssl=ssl))
    except KeyboardInterrupt:
        pass


def parse_channel(s: str) -> Channel:
    return Channel(name=s)


def get_default_channels() -> list[Channel]:
    return [Channel("general")]


def parse_cert(s: str) -> ssl.SSLContext | None:
    if s == "":
        return

    cafile, _, keyfile = s.partition(":")
    keyfile = keyfile or None

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cafile, keyfile)
    return context


async def host_server(
    state: ServerState,
    host: str | None,
    port: int,
    *,
    ssl: ssl.SSLContext | None,
) -> None:
    manager = Manager(state, ssl)
    server = await asyncio.start_server(
        manager.accept_connection,
        host=host,
        port=port,
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    main()
