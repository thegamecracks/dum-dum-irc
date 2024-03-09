import asyncio
import concurrent.futures
import threading
from typing import Self


class EventThread(threading.Thread):
    """Handles starting and stopping an asyncio event loop in a separate thread."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.loop_fut = concurrent.futures.Future()
        self.stop_fut = concurrent.futures.Future()
        self.finished_fut = concurrent.futures.Future()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, tb) -> None:
        self.stop()
        self.join()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.loop_fut.result()

    def run(self) -> None:
        try:
            asyncio.run(self._run_forever())
        finally:
            self.finished_fut.set_result(None)

    def stop(self) -> None:
        if not self.stop_fut.done():
            self.stop_fut.set_result(None)

    async def _run_forever(self) -> None:
        self.loop_fut.set_result(asyncio.get_running_loop())
        await asyncio.wrap_future(self.stop_fut)
