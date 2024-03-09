"""Start the client interface for connecting to dumdum servers."""
from __future__ import annotations

import argparse

from .app import TkApp
from .connect_frame import ConnectFrame
from .event_thread import EventThread


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    args = parser.parse_args()

    with EventThread() as event_thread:
        app = TkApp(event_thread)
        app.switch_frame(ConnectFrame(app))
        app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
