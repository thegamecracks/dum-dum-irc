# dum-dum-irc

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/dum-dum-irc/pyright-lint.yml?style=flat-square&label=pyright)](https://microsoft.github.io/pyright/#/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/dum-dum-irc/python-test.yml?style=flat-square&logo=pytest&label=tests)](https://docs.pytest.org/en/stable/)

A handcrafted implementation of an internet relay chat without following
any conventions or RFC standards.

![Two client windows side-by-side](/docs/images/demo.png)

## Usage

With Python 3.11+ and Git installed, you can run the following:

```sh
pip install git+https://github.com/thegamecracks/dum-dum-irc@v0.1.3
```

Once installed, the `dumdum` and `dumdum-server` entry points should be
provided. Run `dumdum-server --help` for options.

## Implementation

Dumdum consists of two parts:

1. The Sans-IO protocol, defined in [dumdum.protocol]
2. The asyncio wrapper, defined in [dumdum.client] and [dumdum.server]

The [Sans-IO] protocol is responsible for handling the generation and
consumption of byte streams, along with producing events from received
messages, while the asyncio wrapper is responsible for the actual network
communication between the server and its clients.

[Sans-IO]: https://sans-io.readthedocs.io/

[dumdum.protocol]: /src/dumdum/protocol/
[dumdum.client]: /src/dumdum/client/
[dumdum.server]: /src/dumdum/server.py

## Protocol

Clients are able to send the following messages:

1. AUTHENTICATE: `0x00 | 1-byte version | varchar nickname (32)`
2. SEND_MESSAGE: `0x01 | varchar channel name (32) | varchar content (1024)`
3. LIST_CHANNELS: `0x02`

Clients must send an AUTHENTICATE command before they can begin chat
communications.

Servers are able to send the following messages:

1. INCOMPATIBLE_VERSION: `0x00 | 1-byte version`
2. ACKNOWLEDGE_AUTHENTICATION: `0x01 | 0 or 1 success`
3. SEND_MESSAGE: `0x02 | 8-byte snowflake | varchar channel name (32) | varchar nickname (32) | varchar content (1024)`
4. LIST_CHANNELS: `0x03 | 2-byte length | varchar channel name (32) | ...`

When the client disconnects and reconnects, they MUST re-authenticate with the server.

As this protocol has been intentionally designed to be simple (no timeouts
or keep alives), I/O wrappers do not need a significant amount of work to
implement it.
