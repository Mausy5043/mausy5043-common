#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Common functions for use with Sessy home batteries."""

import asyncio
import logging

from sessypy.devices import SessyBattery, SessyDevice, SessyP1Meter, get_sessy_device

LOGGER: logging.Logger = logging.getLogger(__name__)


async def run():
    devices = list()

    devices.append(
        await get_sessy_device(
            SESSY_BATTERY1_HOST, SESSY_BATTERY1_USERNAME, SESSY_BATTERY1_PASSWORD
        )
    )
    devices.append(
        await get_sessy_device(
            SESSY_BATTERY2_HOST, SESSY_BATTERY2_USERNAME, SESSY_BATTERY2_PASSWORD
        )
    )
    devices.append(await get_sessy_device(SESSY_P1_HOST, SESSY_P1_USERNAME, SESSY_P1_PASSWORD))
    device: SessyDevice
    for device in devices:
        print(f"=== Sessy Device at {device.host} ===")
        print(f"S/N: {device.serial_number}")
        print("- Network status -")
        result = await device.get_network_status()
        print(result)
        print("")

        print("- Software update status -")
        result = await device.get_ota_status()
        print(result)
        print("")

        if isinstance(device, SessyBattery):
            print("- Power Status -")
            result = await device.get_power_status()
            print(result)
            print("")

            print("- Power Strategy -")
            result = await device.get_power_strategy()
            print(result)
            print("")

            print("- System settings -")
            result = await device.get_system_settings()
            print(result)
            print("")

            print("- Dynamic mode schedule -")
            result = await device.get_dynamic_schedule()
            print(result)
            print("")

        elif isinstance(device, SessyP1Meter):
            print("- P1 Status -")
            result = await device.get_p1_details()
            print(result)
            print("")

        await device.close()


asyncio.run(run())
