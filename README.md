# dum-dum-irc

[![](https://img.shields.io/pypi/v/dum-dum-irc?style=flat-square)](https://pypi.org/project/dum-dum-irc/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/dum-dum-irc/pyright-lint.yml?style=flat-square&label=pyright)](https://microsoft.github.io/pyright/#/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/dum-dum-irc/python-test.yml?style=flat-square&logo=pytest&label=tests)](https://docs.pytest.org/en/stable/)

A handcrafted implementation of an internet relay chat without following
any conventions or RFC standards.

![](https://raw.githubusercontent.com/thegamecracks/dum-dum-irc/main/docs/images/demo.png)

### [Changelog] | [Contributing Guide]

[Changelog]: https://github.com/thegamecracks/dum-dum-irc/blob/main/CHANGELOG.md
[Contributing Guide]: https://github.com/thegamecracks/dum-dum-irc/blob/main/CONTRIBUTING.md

## Usage

With Python 3.11+ installed, you can get the current stable version on PyPI:

```sh
pip install dum-dum-irc
```

Or if you have Git, you can install the latest in-development version:

```sh
pip install git+https://github.com/thegamecracks/dum-dum-irc
```

Once installed, you can use the `dumdum` and `dumdum-server` commands.
Running `dumdum` starts a graphical client which you can use to join
Dumdum servers, while `dumdum-server` is used to host servers of your own.
Both support the `-h/--help` option if you want to see more details:

```sh
usage: dumdum [-h] [-v] {appdirs} ...

Start the client interface for connecting to dumdum servers.

positional arguments:
  {appdirs}

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase logging verbosity
```

```sh
usage: dumdum-server [-h] [-v] [-c CHANNELS [CHANNELS ...]] [--host HOST] [--port PORT] [--cert CERT]

Host a dumdum server.

To use TLS encryption, you must provide a certificate and private key.
This can be specified as either:
1. A single file containing both the private key and certificate:
     --cert hello.pem
2. A pair of certificate and private key files, separated with a colon:
     --cert hello.crt:hello.key

options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase logging verbosity
  -c CHANNELS [CHANNELS ...], --channels CHANNELS [CHANNELS ...]
                        A list of channels
  --host HOST           The address to host on, or all interfaces when not supplied
  --port PORT           The port number to host on (default: 6667)
  --cert CERT           The SSL certificate and private key to use
```

## Implementation

Dumdum consists of two parts:

1. The Sans-IO protocol, defined in [dumdum.protocol]
2. The asyncio wrapper, defined in [dumdum.client] and [dumdum.server]

The [Sans-IO] protocol is responsible for handling the generation and
consumption of byte streams, along with producing events from received
messages, while the asyncio wrapper is responsible for the actual network
communication between the server and its clients.

[Sans-IO]: https://sans-io.readthedocs.io/

[dumdum.protocol]: https://github.com/thegamecracks/dum-dum-irc/tree/main/src/dumdum/protocol
[dumdum.client]: https://github.com/thegamecracks/dum-dum-irc/tree/main/src/dumdum/client
[dumdum.server]: https://github.com/thegamecracks/dum-dum-irc/tree/main/src/dumdum/server

## Protocol

Clients are able to send the following messages:

1. HELLO: `0x00 | 1-byte version`
2. AUTHENTICATE: `0x02 | varchar nickname (32)`
3. SEND_MESSAGE: `0x03 | varchar channel name (32) | varchar content (1024)`
4. LIST_CHANNELS: `0x04`
5. LIST_MESSAGES: `0x05 | 8-byte before snowflake or 0 | 8-byte after snowflake or 0`

Servers are able to send the following messages:

1. HELLO: `0x00 | 0 or 1 using SSL`
2. INCOMPATIBLE_VERSION: `0x01 | 1-byte version`
3. ACKNOWLEDGE_AUTHENTICATION: `0x02 | 0 or 1 success`
4. SEND_MESSAGE: `0x03 | 8-byte snowflake | varchar channel name (32) | varchar nickname (32) | varchar content (1024)`
5. LIST_CHANNELS: `0x04 | 2-byte length | varchar channel name (32) | ...`
6. LIST_MESSAGES: `0x05 | 3-byte length | same fields after SEND_MESSAGE | ...`

Clients must send a HELLO command and wait for the server to respond with HELLO.
Afterwards the client must send an AUTHENTICATE command and wait for a successful
ACKNOWLEDGE_AUTHENTICATION before they can begin chat communications.

When the client disconnects and reconnects, they MUST re-send hello
and re-authenticate with the server.

If the server supports SSL, they can set `using SSL` in HELLO to indicate
that the client should upgrade the connection to SSL.
At this point, the protocol should not receive any data until after the
SSL handshake is complete.

As this protocol has been intentionally designed to be simple (no timeouts
or keep alives), I/O wrappers do not need a significant amount of work to
implement it.

## TLS Encryption

`dumdum-server` can use SSL certificates to encrypt connections.
For example, if you want to use a self-signed certificate and private key,
you can install OpenSSL and run the following command:

```sh
openssl req -new -x509 -days 365 -noenc -out dumdum.crt -keyout dumdum.key
```

After filling out (or skipping) the certificate signing request prompts,
you can then run the server with the resulting `dumdum.crt` and `dumdum.key`
files:

```sh
dumdum-server --cert dumdum.crt:dumdum.key
```

As for the `dumdum` client, SSL can be enabled by the user before connecting
to a server. If the server uses a self-signed certificate, the user will need
to download the server's certificate (.crt) and select it.
