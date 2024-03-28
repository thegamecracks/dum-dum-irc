"""Start the client interface for connecting to dumdum servers."""

from __future__ import annotations

import argparse
import contextlib
import sys
from typing import Iterator

from dumdum.logging import configure_logging

from .app import TkApp
from .connect_frame import ConnectFrame
from .event_thread import EventThread
from .store import ClientStore


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
    parser.set_defaults(mode="gui")

    commands = parser.add_subparsers()

    appdirs = commands.add_parser(
        "appdirs",
        description="Show data directories used by dumdum.",
    )
    appdirs.set_defaults(mode="appdirs")

    args = parser.parse_args()
    verbose: int = args.verbose
    mode: str = args.mode

    configure_logging("client", verbose)
    enable_windows_dpi_awareness()

    if mode == "gui":
        with contextlib.suppress(KeyboardInterrupt):
            run_gui()
    elif mode == "appdirs":
        show_appdirs()
    else:
        raise RuntimeError(f"Unknown mode {mode!r}")


def run_gui() -> None:
    with EventThread() as event_thread:
        app = TkApp(
            event_thread=event_thread,
            store_factory=store_factory,
        )
        app.switch_frame(ConnectFrame(app))

        try:
            app.mainloop()
        except BaseException:
            app.destroy()
            app.mainloop()
            raise


def enable_windows_dpi_awareness():
    if sys.platform == "win32":
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(2)


def show_appdirs() -> None:
    from dumdum.appdirs import APP_DIRS

    print("user_data_path =", APP_DIRS.user_data_path)
    print("user_log_path =", APP_DIRS.user_log_path)


@contextlib.contextmanager
def store_factory() -> Iterator[ClientStore]:
    with ClientStore.from_appdirs() as store, store.transaction():
        yield store


if __name__ == "__main__":
    main()
