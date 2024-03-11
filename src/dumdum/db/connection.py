import contextlib
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, ContextManager, Iterator, Protocol, Self, Sequence

Row = Sequence[Any]


class Cursor(Protocol):
    def fetchone(self) -> Row: ...
    def fetchall(self) -> Sequence[Row]: ...


class Connection(ABC):
    @abstractmethod
    def execute(self, query: str, /, *parameters: Any) -> Cursor:
        """Execute query and return a cursor."""

    @abstractmethod
    def executescript(self, query: str, /) -> None:
        """Execute one or more SQL statements."""

    @abstractmethod
    def transaction(self) -> ContextManager[Self]:
        """Returns a context manager to begin a transaction."""

    def fetchone(self, query: str, /, *parameters: Any) -> Row | None:
        """Execute query and return the first row.

        If the results are empty, None is returned.

        """
        c = self.execute(query, *parameters)
        return c.fetchone()

    def fetchall(self, query: str, /, *parameters: Any) -> Sequence[Row]:
        """Execute query and return all rows.

        If the results are empty, None is returned.

        """
        c = self.execute(query, *parameters)
        return c.fetchall()

    def fetchval(self, query: str, /, *parameters: Any) -> Any:
        """Execute query and return the first value of the first row.

        If the results are empty, None is returned.

        """
        row = self.fetchone(query, *parameters)
        if row is not None:
            return row[0]


class SQLiteConnection(Connection):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, query: str, *parameters: Any) -> sqlite3.Cursor:
        if len(parameters) == 1 and isinstance(parameters[0], (tuple, list, dict)):
            _params = parameters[0]
        else:
            _params = parameters

        return self._conn.execute(query, _params)

    def executescript(self, query: str) -> None:
        self._conn.executescript(query)

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Self]:
        with self._conn:
            yield self

    @classmethod
    @contextlib.contextmanager
    def connect(cls, *args, **kwargs) -> Iterator[Self]:
        with contextlib.closing(sqlite3.connect(*args, **kwargs)) as conn:
            yield cls(conn)
