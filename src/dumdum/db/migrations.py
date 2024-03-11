import logging
import re
from typing import Literal

import importlib_resources

from .connection import SQLiteConnection

log = logging.getLogger(__name__)

MigrationPath = Literal["client"]


def run_migrations(conn: SQLiteConnection, path: MigrationPath):
    version: int = conn.fetchval("PRAGMA user_version")
    script_version = version

    for script_version, script in _get_migrations(path, version).items():
        conn.executescript(script)

    if script_version > version:
        conn.execute(f"PRAGMA user_version = {script_version}")
        log.debug("Migrated database v%d to v%d", version, script_version)


def _get_migrations(path: MigrationPath, version: int) -> dict[int, str]:
    migrations: dict[int, str] = {}

    resource = importlib_resources.files(__package__) / "scripts" / path
    with importlib_resources.as_file(resource) as root:
        for file in root.glob("*.sql"):
            m = re.match(r"\d+", file.stem)
            if m is None:
                continue

            file_version = int(m[0])
            if file_version in migrations:
                raise ValueError(
                    f"Duplicate migration found for version {file_version}"
                )

            if file_version <= version:
                continue

            migrations[file_version] = file.read_text("utf-8")

    return dict(sorted(migrations.items()))
