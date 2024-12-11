# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.3] - 2024-12-11

### Changed

- Limit server message cache to 1000 per channel, configurable with `--max-messages`

## [0.4.2] - 2024-06-17

### Added

- Connection menu to allow disconnecting from servers without restarting the client

### Changed

- Clarify default host/port arguments for `dumdum-server`
- Limit client message cache to 1000 per channel

## [0.4.1] - 2024-04-04

### Added

- Write/close timeouts for asyncio client and server
  - This should mitigate deadlocks caused by excessive backpressure
    on both sides of a connection.
- Buffer limits for client and server protocols
  - This defaults to 1MiB, but can be customized or disabled via the
    `buffer_size=` parameter. Upon exceeding the protocol's buffer,
    the `receive_bytes()` method will raise `BufferOverflowError`
    indicating that the connection should be terminated.

## [0.4.0.post1] - 2024-03-30

This release updates the readme to start referring to our new PyPI distribution! 🎉

## [0.4.0] - 2024-03-30

### Added

- Write `.jsonl` client and server logs to a user log directory
  - Defaults to INFO logs and above, but can be set to DEBUG with `-vv`
- Add user log directory to `dumdum appdirs` command

### Changed

- Rename distribution package name to `dum-dum-irc`
  - Users of older versions must manually uninstall `dum-dum` beforehand,
    otherwise they may co-exist in the same environment and cause files to be
    overwritten.
- Refactor `dumdum.server` into a package
  - `main()` is no longer exported, requiring the `dumdum-server` console script
    to be changed. The package must be reinstalled for this change to apply,
    otherwise `dumdum-server` will raise ImportError.
  - Move `dumdum.protocol.HighCommand` to `dumdum.server.ServerState`
- Dumdum client improvements:
  - Immediately wrap messages when switching between channels
  - Show dedicated error message for unknown self-signed certificates

### Fixed

- Dumdum client not cleanly exiting when being keyboard interrupted

## [0.3.0] - 2024-03-24

Breaking changes were made to the protocol. Connections can now negotiate
TLS encryption before proceeding with authentication via a new HELLO message type.

### Added

- New event/message types:
  - `ClientEventHello`
  - `ClientMessageHello`
  - `ServerEventHello`
  - `ServerMessageHello`
- New `dumdum-server --cert <CERT | CERT:KEY>` argument
- New client GUI configuration options:
  - `Use SSL`
  - `Certificate (Optional)`

### Changed

- Bump protocol version from `1` to `2`
- Re-enumerate `ClientMessageType` values:
  - `HELLO = 0`
  - `AUTHENTICATE = 2`
  - `SEND_MESSAGE = 3`
  - `LIST_CHANNELS = 4`
  - `LIST_MESSAGES = 5`
- Re-enumerate `ServerMessageType` values:
  - `HELLO = 0`
  - `INCOMPATIBLE_VERSION = 1`
  - `AUTHENTICATE = 2`
  - `SEND_MESSAGE = 3`
  - `LIST_CHANNELS = 4`
  - `LIST_MESSAGES = 5`
- Dumdum client improvements:
  - Dynamically wrap message content for larger window sizes
  - Automatically scroll message feed

### Removed

- `ClientMessageAuthenticate.version`
  - This has been moved to `ClientMessageHello`

### Fixed

- Resolve potential deadlock in client GUI when connection terminates
  before authentication is completed

## [0.2.1] - 2024-03-21

### Changed

- Various visual tweaks to the Dumdum client
  - Enable DPI awareness on Windows
  - Show nicknames beside message content in a larger font

### Fixed

- Non-fatal `asyncio.CancelledError` when closing a server with connected clients

## [0.2.0] - 2024-03-20

Several breaking changes were made to the protocol and the Sans I/O protocol
implementation. `Server` no longer takes a `HighCommand` instance.
I/O wrappers will now have to manage their own user state and manually
send the channel list upon receiving the new event, `ServerEventListChannels`.
Servers can now also send a list of messages to their clients,
usually after receiving `ServerEventListMessages`.

### Added

- More test coverage of the protocol
- `Server.authenticate()` method
- `Server.list_channels()` method
- `ServerEventListChannels` type
- `ClientEventMessagesListed` type
- `ClientMessageListMessages` type
- `ServerEventListMessages` type
- `ServerMessageListMessages` type
- `Message` dataclass with ID field
- Message cache to `HighCommand`
- `Reader.read_bigint()` method
- `snowflake.create_snowflake()` function

### Changed

- Bump protocol version from `0` to `1`
- Rename `Client.REQUIRED_VERSION` to `Client.PROTOCOL_VERSION`
- Only accept channel name in `Server.send_message()` method
- Replace `ServerMessagePost.channel` with `.channel_name`
- Replace `ServerEventMessageReceived.channel` with `.channel_name`
- Replace `ClientEventMessageReceived` fields with one message field
- Replace `ServerMessagePost` fields with one message field
- Replace `Server.send_message()` parameters with one message parameter

### Removed

- `Server(hc=)` parameter
- `Server.nick` attribute
  - I/O wrappers must store this
- `Server.close()` method
- `ServerEventAuthentication.success` attribute

### Fixed

- `varchar.dumps()` permitting more data than is allowed by `max_length=` parameter
- Non-fatal `TclError` when connecting to a server whose last selected channel
  has disappeared
- Client GUI showing two error messages when authentication fails

## [0.1.3] - 2024-03-11

### Added

- SQLite database in user data directory for persisting settings
  - Last selected channel per host/port
  - Last address/port/nickname
  - Added `dumdum appdirs` command to show the user data directory path

## [0.1.2] - 2024-03-10

### Added

- Usage section to README.md

### Fixed

- Non-fatal `asyncio.CancelledError` when closing client GUI
- Non-fatal `tkinter.TclError` when GUI connects to server
- Catch `KeyboardInterrupt` in server CLI

## [0.1.1] - 2024-03-09

### Added

- Summary of implementation and protocol in README.md
- `dumdum` and `dumdum-server` console scripts

### Fixed

- Ignore unauthenticated users when broadcasting messages

## [0.1.0] - 2024-03-09

### Added

- Initial protocol implementation
  - Authentication
  - Nickname conflict prevention
  - Channel listing
  - Sending messages to channels
- `dumdum.server` asyncio server CLI
- `dumdum.client` asyncio tkinter GUI client
- GitHub workflows for pyright and pytest

[Unreleased]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.4.3...main
[0.4.3]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.4.0.post1...v0.4.1
[0.4.0.post1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.4.0...v0.4.0.post1
[0.4.0]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thegamecracks/dum-dum-irc/releases/tag/v0.1.0
