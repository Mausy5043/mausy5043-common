#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Common functions for use with Sessy home batteries."""

import asyncio
import logging

from sessypy.devices import (  # type: ignore[import-untyped]
    SessyDevice,
    get_sessy_device,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class Sessy_v1:  # pylint: disable=too-many-instance-attributes
    """Class to interact with the Sessy Battery."""

    def __init__(self, ip: str, username: str, password: str, debug: bool = False) -> None:
        """."""
        self.api_version: str = "v1"
        self.ip: str = ip
        self.dev_name: str = "unknown"
        self.dev_ota: dict = {}
        self.username: str = username
        self.password: str = password
        self.debug: bool = debug

        self.dev_device: SessyDevice | None = None
        self.dev_measurement: dict = {}
        self.dev_schedule: dict = {}

    async def aget_device(self) -> None:
        """Get basic device information, like firmware version."""
        self.dev_device = await get_sessy_device(
            host=self.ip, username=self.username, password=self.password
        )
        if self.dev_device:
            self.dev_ota = await self.dev_device.get_ota_status()
            self.dev_name = self.dev_device.serial_number
        else:
            raise ValueError("Device is not initialized.")
        await self.dev_device.close()
        LOGGER.debug("")

    async def aget_measurement(self) -> None:
        """Fetch a telegram from the P1 dongle."""
        # async with HomeWizardEnergyV1(host=self.ip) as _api:
        # Get measurements
        self.dev_device = await get_sessy_device(
            host=self.ip, username=self.username, password=self.password
        )
        if self.dev_device:
            self.dev_measurement = await self.dev_device.get_power_status()
        else:
            raise ValueError("Device is not initialized.")
        await self.dev_device.close()
        LOGGER.debug(self.dev_measurement)
        LOGGER.debug("---")

    async def aget_schedule(self) -> None:
        """Fetch the dynamic schedule."""
        self.dev_device = await get_sessy_device(
            host=self.ip, username=self.username, password=self.password
        )
        if self.dev_device:
            self.dev_schedule = await self.dev_device.get_dynamic_schedule()
        else:
            raise ValueError("Device is not initialized.")
        await self.dev_device.close()
        LOGGER.debug(self.dev_schedule)
        LOGGER.debug("---")


class MySessyBattery:
    """Class to interact with the Sessy batteries."""

    def __init__(self, ip: str, user: str, token: str, debug: bool = False) -> None:
        """Initialize the MySessyBattery class.

        Args:
            ip (str): The IP of the battery.
            user (str): The username for the battery.
            token (str): The password for the battery.
            debug (bool, optional): If True, debugging mode is enabled.

        """
        self.debug: bool = debug
        self.ip: str = ip
        self.username: str = user
        self.password: str = token
        self.connection: Sessy_v1 | None = None
        self.api_version: str = "unknown"

    def connect(self) -> None:
        """Acquire a connection to the Sessy battery."""
        self.connection = Sessy_v1(
            ip=self.ip, username=self.username, password=self.password, debug=self.debug
        )
        if self.connection:
            asyncio.run(self.connection.aget_device())
        else:
            raise ValueError("No connection to battery established.")
        LOGGER.info(f"Connected to device: {self.connection.dev_name}")
        LOGGER.info(f"Device info: {self.connection.dev_ota}")

    def get_measurement(self) -> dict:
        """Get the measurement from the battery.

        Returns:
            dict: A dictionary containing the translated measurement data.
        """
        if self.connection:
            asyncio.run(self.connection.aget_measurement())
        else:
            raise ValueError("No connection to battery established.")
        return self.connection.dev_measurement

    def get_schedule(self) -> dict:
        """Get the schedule from the battery.

        Returns:
            dict: A dictionary containing the dynamic schedule data.
        """
        if self.connection:
            asyncio.run(self.connection.aget_schedule())
        else:
            raise ValueError("No connection to battery established.")
        return self.connection.dev_schedule


if __name__ == "__main__":
    import json
    import os
    import sys

    _MYHOME: str = os.environ["HOME"]
    config_file = f"{_MYHOME}/.config/sessy.json"
    # process config file
    try:
        with open(config_file, encoding="utf-8") as _json_file:
            _cfg = json.load(_json_file)
    except FileNotFoundError:
        LOGGER.error(f"'{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        LOGGER.error("Error decoding JSON config file.")
        sys.exit(1)
    for battery in ["bat1", "bat2"]:
        try:
            bat_ip: str = _cfg[battery]["ip"]
            bat_usr: str = _cfg[battery]["username"]
            bat_pwd: str = _cfg[battery]["password"]
        except KeyError as her:
            LOGGER.error(f"KeyError: {her}")
            LOGGER.error("Please check the config file.")
            sys.exit(1)
        # Test the Sessy class
        myses = MySessyBattery(ip=bat_ip, user=bat_usr, token=bat_pwd, debug=True)
        myses.connect()
        print(json.dumps(myses.get_measurement(), indent=1, sort_keys=True))
        # print(json.dumps(myses.get_schedule(), indent=1, sort_keys=True))
