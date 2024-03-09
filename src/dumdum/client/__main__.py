"""Start the client interface for connecting to dumdum servers."""
from __future__ import annotations

import argparse

from dumdum.logging import configure_logging

from .app import TkApp
from .connect_frame import ConnectFrame
from .event_thread import EventThread


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

    args = parser.parse_args()
    verbose: int = args.verbose

    configure_logging(verbose)

    with EventThread() as event_thread:
        app = TkApp(event_thread)
        app.switch_frame(ConnectFrame(app))
        app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
