#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Provide a generic class to interact with an sqlite3 database."""

import logging
import logging.handlers
import os
import sqlite3 as s3
import time

import pandas as pd

DT_FORMAT = "%Y-%m-%d %H:%M:%S"

LOGGER: logging.Logger = logging.getLogger(__name__)


class SqlDatabase:  # pylint: disable=R0902
    """A class to interact with SQLite3 databases."""

    def __init__(
        self,
        database: str,
        table: str,
        insert: str,
        schema: str = "",
        debug: bool = False,
    ) -> None:
        """Initialise database queue object."""
        self.debug: bool = debug
        self.home: str = os.environ["HOME"]
        self.version: float = 3.0
        self.database: str = database
        self.schema: str = schema
        self.table: str = table
        self.sql_insert: str = insert
        self.sql_query: str = ""
        self.dataq: list[dict] = []
        self.db_version: str = self._test_db_connection()

    def _test_db_connection(self) -> str:
        """Print the version of the database.

        Returns:
            version of the database
        """
        consql: s3.Connection | None = None
        try:
            consql = s3.connect(self.database, timeout=9000)
        except s3.Error as her:
            LOGGER.critical(
                f"Unexpected error of type {type(her).__name__} when connecting to server."
            )
            # LOGGER.info(traceback.format_exc())   # raise already does this
            if consql:  # attempt to close connection to sqlite3 server
                consql.close()
                LOGGER.debug(" ** Closed SQLite3 connection. **")
            raise
        cursor: s3.Cursor = consql.cursor()
        try:
            cursor.execute("SELECT sqlite_version();")
            versql: str = str(cursor.fetchone())
            cursor.close()
            consql.commit()
            consql.close()
            LOGGER.info(f"Attached to SQLite3 server: {versql}")
            LOGGER.info(f"Using DB file             : {self.table}@{self.database}")
        except s3.Error as her:
            LOGGER.critical(f"Unexpected SQLite3 error of type {type(her).__name__} during test.")
            # LOGGER.info(traceback.format_exc())   # raise already does this
            raise
        return versql

    def queue(self, data: dict) -> None:
        """Append data to the queue for insertion.

        Args:
            data (dict): data to be inserted

        Returns:
            None
        """
        if isinstance(data, dict):
            self.dataq.append(data)
            LOGGER.debug(f"Queued : {data}")
        else:
            # LOGGER.critical("Data must be a dictionary!")   # raise already does this
            raise TypeError("Data must be a dictionary")

    def insert(self, method: str = "ignore", index: str = "sample_time") -> None:
        """Commit queued data to the database.

        Args:
            method (str):   how to handle duplicates in the database.
                            Possible options are:
                            'ignore' (database will not be changed) or
                            'replace' (existing data will be removed and new data inserted).
            index (str):    name of the field to be used as the index.

        Returns:
            None

        Raises:
            ValueError: if <self.insert> is empty
            sqlite3.Error: when commit fails serverside
            Exception: to catch unknown errors during the exchange
        """
        consql: s3.Connection | None = None
        if self.sql_insert == "":
            raise ValueError("No instruction provided")

        try:
            consql = s3.connect(self.database, timeout=9000)
        except s3.Error as her:
            LOGGER.critical(
                f"Unexpected error of type {type(her).__name__} when connecting to server."
            )
            # LOGGER.info(traceback.format_exc())    # raise already does this
            if consql:  # attempt to close connection to sqlite3 server
                consql.close()
                LOGGER.debug(" ** Closed SQLite3 connection. **")
            raise

        while self.dataq:
            element = self.dataq[0]
            df_idx = index  # list(element.keys())[0]    # this should always be 'sample_time'
            df = pd.DataFrame(element, index=[df_idx])
            try:
                df.to_sql(name=self.table, con=consql, if_exists="append", index=False)
                LOGGER.debug(f"Inserted : \n{df}\n")
            except s3.IntegrityError:
                # probably "sqlite3.IntegrityError: UNIQUE constraint failed".
                # this can be passed
                if method == "ignore":
                    LOGGER.debug("Duplicate entry. Not adding to database.")
                if method == "replace":
                    element_time = element[f"{df_idx}"]
                    # fmt: off
                    sql_command = f'DELETE FROM {self.table} WHERE {df_idx} = "{element_time}";'  # nosec B608
                    # fmt: on
                    cursor = consql.cursor()
                    try:
                        cursor.execute(sql_command)
                        cursor.fetchone()
                        cursor.close()
                        consql.commit()
                    except s3.IntegrityError:
                        # probably "sqlite3.IntegrityError: UNIQUE constraint failed".
                        # this can be passed
                        LOGGER.debug("Ignoring: IntegrityError.")
                        pass
                    except s3.Error as her:
                        LOGGER.critical(
                            f"Error of type {type(her).__name__} when commiting to server."
                        )
                        # LOGGER.info(traceback.format_exc())     # raise already does this
                        raise
                    df.to_sql(name=self.table, con=consql, if_exists="append", index=False)
                    LOGGER.debug(f"Replaced : \n{df}\n")
            except s3.Error as her:
                LOGGER.critical(
                    f"SQLite3 error of type {type(her).__name__} when commiting to server."
                )
                # LOGGER.info(traceback.format_exc())     # raise already does this
                raise
            except Exception as her:
                LOGGER.critical(
                    f"Unexpected error of type {type(her).__name__} when commiting to server."
                )
                # LOGGER.info(traceback.format_exc())     # raise already does this
                raise
            self.dataq.pop(0)

        consql.close()

    def latest_datapoint(self) -> str:
        """Look up last entry in the database table.

        Returns:
            date and time of the youngest entry in the table
        """
        consql: s3.Connection | None = None
        try:
            consql = s3.connect(self.database, timeout=9000)
        except s3.Error as her:
            LOGGER.critical(
                f"Unexpected error of type {type(her).__name__} when connecting to server."
            )
            # LOGGER.info(traceback.format_exc())     # raise already does this
            if consql:  # attempt to close connection to sqlite3 server
                consql.close()
                LOGGER.debug(" ** Closed SQLite3 connection. **")
            raise
        cursor: s3.Cursor = consql.cursor()
        try:
            sql_command = f"SELECT MAX(sample_epoch) from {self.table};"  # nosec B608
            cursor.execute(sql_command)
            max_epoch = cursor.fetchone()
            human_epoch = time.localtime(max_epoch[0])
            cursor.close()
            consql.commit()
            consql.close()
            LOGGER.debug(
                f"Latest datapoint in {self.table}: "
                f"{max_epoch[0]} = {time.strftime('%Y-%m-%d %H:%M:%S', human_epoch)}"
            )
        except s3.Error as her:
            LOGGER.critical(f"Unexpected SQLite3 error of type {type(her).__name__} during test.")
            # LOGGER.info(traceback.format_exc())     # raise already does this
            raise
        return time.strftime("%Y-%m-%d %H:%M:%S", human_epoch)
