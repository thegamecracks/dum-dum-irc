# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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

[Unreleased]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.2.1...main
[0.2.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thegamecracks/dum-dum-irc/releases/tag/v0.1.0
