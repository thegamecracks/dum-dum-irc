# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Several breaking changes were made to the protocol and the Sans I/O protocol
implementation. `Server` no longer takes a `HighCommand` instance.
I/O wrappers will now have to manage their own user state and manually
send the channel list upon receiving the new event, `ServerEventListChannels`.
Servers can now also send a list of messages to their clients,
usually after receiving `ServerEventListMessages`.

### Added

- More test coverage of the protocol
- `Server.acknowledge_authentication()` method
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

[Unreleased]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.3...main
[0.1.3]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/thegamecracks/dum-dum-irc/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thegamecracks/dum-dum-irc/releases/tag/v0.1.0