import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def initialize():
    with connect() as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
