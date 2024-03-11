import contextlib
from typing import Any, Iterator, Self, TypeVar

from dumdum.appdirs import APP_DIRS
from dumdum.db import SQLiteConnection, run_migrations

T = TypeVar("T")


class ClientStore:
    def __init__(self, conn: SQLiteConnection) -> None:
        self.conn = conn

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Self]:
        with self.conn.transaction():
            yield self

    def get_last_selected_channel(
        self,
        addr: str,
        default: str | T = None,
    ) -> str | T:
        ret = self.conn.fetchval(
            "SELECT channel_name FROM last_selected_channel WHERE addr = ?",
            addr,
        )
        if ret is None:
            return default
        return ret

    def set_last_selected_channel(
        self, addr: str, channel_name: str | None = None
    ) -> None:
        self.conn.execute(
            "INSERT INTO last_selected_channel (addr, channel_name) VALUES (?1, ?2) "
            "ON CONFLICT (addr) DO UPDATE SET channel_name = ?2",
            addr,
            channel_name,
        )

    def get_setting(self, name: str, default: Any = None) -> Any:
        row = self.conn.fetchone("SELECT value FROM setting WHERE name = ?", name)
        if row is None:
            return default
        return row[0]

    def set_setting(self, name: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO setting (name, value) VALUES (?1, ?2) "
            "ON CONFLICT (name) DO UPDATE SET value = ?2",
            name,
            value,
        )

    @classmethod
    @contextlib.contextmanager
    def from_appdirs(cls) -> Iterator[Self]:
        path = APP_DIRS.user_data_path / "client.db"
        with SQLiteConnection.connect(str(path)) as conn:
            with conn.transaction():
                run_migrations(conn, "client")

            yield cls(conn)
