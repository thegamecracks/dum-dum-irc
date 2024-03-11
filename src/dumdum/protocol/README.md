This contains the [Sans-IO] implementation of the Dumdum protocol.

- [`client/`](client/): Implements the client side of the protocol.
- [`server/`](server/): Implements the server side of the protocol.
- [`channel.py`](channel.py): A basic channel dataclass shared between the client and server.
- [`constants.py`](constants.py): Defines a few constants used by the protocol.
- [`enums.py`](enums.py): Defines the message types that will be sent between the client and server.
- [`errors.py`](errors.py): Defines exceptions that the protocol can raise.
- [`highcommand.py`](highcommand.py): A server-side, in-memory datastore for channels and users.
- [`interfaces.py`](interfaces.py): Defines a common interface between the client and server.
- [`reader.py`](reader.py): Provides functions to read through bytes/bytearrays like streams.
- [`varchar.py`](varchar.py): Provides functions to de/serialize variable-length strings.

[Sans-IO]: https://sans-io.readthedocs.io/
