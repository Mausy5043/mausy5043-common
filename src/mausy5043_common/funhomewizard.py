#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

# https://api-documentation.homewizard.com/docs/category/api-v1

"""Common functions for use with HomeWizard devices using."""

import asyncio
import json
import logging

import homewizard_energy.models as hwem
from homewizard_energy import HomeWizardEnergyV1, HomeWizardEnergyV2

try:
    from . import funzeroconf as zcd
except ImportError:
    import funzeroconf as zcd  # type: ignore


LOGGER: logging.Logger = logging.getLogger(__name__)


D_FORMAT = "%Y-%m-%d"
DT_FORMAT = "%Y-%m-%d %H:%M:%S"

SUPPORTED_SERVICES = {"v1": "_hwenergy", "v2": "_homewizard"}
SUPPORTED_VERSIONS = {_v: _k for _k, _v in SUPPORTED_SERVICES.items()}

# https://api-documentation.homewizard.com/docs/category/api-v1


class HomeWizard_V1:  # pylint: disable=too-many-instance-attributes
    """Class to interact with the Home Wizard P1-dongle."""

    def __init__(self, ip: str, debug: bool = False) -> None:  # pylint: disable=too-many-instance-attributes
        """."""
        self.api_version = "v1"
        self.ip = ip
        self.debug: bool = debug

        self.dev_device: hwem.Device | None = None
        self.dev_measurement: hwem.Measurement | None = None

        self.dt_format: str = DT_FORMAT

    async def aget_device(self) -> None:
        """Get basic device information, like firmware version."""
        async with HomeWizardEnergyV1(host=self.ip) as _api:
            self.dev_device = await _api.device()
            LOGGER.debug(self.dev_device)
            LOGGER.debug("")

    async def aget_measurement(self) -> None:
        """Fetch a telegram from the P1 dongle."""
        async with HomeWizardEnergyV1(host=self.ip) as _api:
            # Get measurements
            self.dev_measurement = await _api.measurement()
            LOGGER.debug(self.dev_measurement)
            LOGGER.debug("---")

    # def _translate_telegram(self, telegram) -> dict:
    #     """Translate the telegram to a dict.
    #
    #     kW or kWh are converted to W resp. kW
    #
    #     Returns:
    #         (dict): data converted to a dict.
    #     """
    #     self.electra1in = int(telegram.energy_import_t1_kwh * 1000)
    #     self.electra2in = int(telegram.energy_import_t2_kwh * 1000)
    #     self.electra1out = int(telegram.energy_export_t1_kwh * 1000)
    #     self.electra2out = int(telegram.energy_export_t2_kwh * 1000)
    #     self.tarif = telegram.tariff
    #     self.powerin = telegram.power_w
    #     self.powerout = 0.0
    #     self.swits = 1
    #     if self.powerin < 0.0:
    #         self.swits = 0
    #         self.powerout = self.powerin
    #         self.powerin = 0.0
    #
    #     idx_dt: dt.datetime = dt.datetime.now()
    #     epoch = int(idx_dt.timestamp())
    #
    #     return {
    #         "sample_time": idx_dt.strftime(self.dt_format),
    #         "sample_epoch": epoch,
    #         "T1in": self.electra1in,
    #         "T2in": self.electra2in,
    #         "powerin": self.powerin,
    #         "T1out": self.electra1out,
    #         "T2out": self.electra2out,
    #         "powerout": self.powerout,
    #         "tarif": self.tarif,
    #         "swits": self.swits,
    #     }


# https://api-documentation.homewizard.com/docs/category/api-v2


class HomeWizard_V2(HomeWizard_V1):
    """Class to interact with a HomeWizard device via the API/v2."""

    def __init__(self, ip: str, token: str, debug: bool = False) -> None:
        """."""
        super().__init__(ip=ip, debug=debug)
        self.api_version = "v2"
        self.token = token

    async def aget_device(self) -> None:
        """Get basic device information, like firmware version."""
        async with HomeWizardEnergyV2(host=self.ip, token=self.token) as _api:
            self.dev_device = await _api.device()
            LOGGER.debug(self.dev_device)
            LOGGER.debug("")

    async def aget_measurement(self) -> None:
        """Fetch a telegram from the P1 dongle."""
        async with HomeWizardEnergyV2(host=self.ip, token=self.token) as _api:
            # Get measurements
            self.dev_measurement = await _api.measurement()
            LOGGER.debug(self.dev_measurement)
            LOGGER.debug("---")


class MyHomeWizard:
    """Class to interact with the Home Wizard devices, regardless of the API version.

    This class is designed to discover HomeWizard devices on the network and
    establish a connection to the appropriate API version based on the device's
    capabilities. It handles the discovery of devices, filtering them based on
    supported services, and finding a specific device by its serial number.
    The class also provides a method to connect to the device using the
    appropriate API version (v1 or v2).
    """

    def __init__(self, serial: str, token: str = "", debug: bool = False) -> None:  # nosec B107
        """Find a device with the given serial number.

        Attributes:
            debug (bool): A flag that determines if debugging mode is active.
            discovered_devices (list): A list of all devices discovered during
                the zeroconf discovery process.
            supported_devices (list): A filtered list of devices limited to
                HomeWizard services.
            serial (str): The unique serial number of the target device.
            target_device: The device corresponding to the provided serial
                number.

        Args:
            serial (str): The serial number of the device to be identified among
                the supported devices.
            debug (bool, optional): If True, debugging mode is enabled.

        Raises:
            ValueError: If no device matching the given serial number is found
                among the supported devices.
        """
        self.debug = debug
        self.serial = serial
        self.token = token
        self.connection: HomeWizard_V1 | HomeWizard_V2 | None = None
        self.api_version: str = "unknown"

        # discover all zeroconf devices
        self.discovered_devices = zcd.discover_devices(search_time=15.0)
        # prune the discovered devices to only the supported ones (homewizard)
        _svcs = [_svc for _v, _svc in SUPPORTED_SERVICES.items()]
        self.supported_devices = zcd.prune_services(self.discovered_devices, _svcs)
        # find the homewizard device that has the requested serial number
        self.target_device = self.__find_serial(
            devices=self.supported_devices, serial=self.serial
        )
        if not self.target_device:
            raise ValueError(f"No device found with serial number {self.serial}")

    @staticmethod
    def __find_serial(devices: dict, serial: str) -> dict:
        """Return information about a HomeWizard device.

        Using a dictionary containing the (zeroconf) devices discovered during the
        initialisation of the class object, this function will search for the device
        with the specified serial number and returns it's information.

        Args:
            devices (dict): A dictionary containing devices as keys and their associated
                services as values. Each service must contain a "properties" field with its serial.
            serial (str): The serial number to search for among the devices.

        Returns:
            dict: A dictionary containing the device and its service(s) found matching
            the specified serial.
            If no match is found, an empty dictionary is returned.
        """
        _product = {}
        for _d in devices:
            for _svc in devices[_d]:
                if devices[_d][_svc]["properties"]["serial"] == serial:
                    _product[_d] = devices[_d]
                    break
        return _product

    def connect(self) -> None:
        """Acquire a connection to the HomeWizard device."""
        _name = list(self.target_device)[0]
        try:
            if self.token:
                _svc = SUPPORTED_SERVICES["v2"]
                _ip = self.target_device[_name][_svc]["ip"]
                self.connection = HomeWizard_V2(ip=_ip, token=self.token, debug=self.debug)
                asyncio.run(self.connection.aget_device())
            else:
                raise ValueError("No valid provided.")
        except (Exception, ValueError) as her:
            LOGGER.warning(f"Falling back to using API/v1 due to: {her}")
            _svc = SUPPORTED_SERVICES["v1"]
            _ip = self.target_device[_name][_svc]["ip"]
            self.connection = HomeWizard_V1(ip=_ip, debug=self.debug)
            asyncio.run(self.connection.aget_device())
        self.api_version = self.connection.api_version
        LOGGER.info(f"Connected to API/{self.api_version} on device: {self.target_device}")
        LOGGER.info(f"Device info: {self.connection.dev_device}")

    def get_measurement(self) -> hwem.Measurement | None:
        """Get the measurement from the HomeWizard device.

        This method retrieves the measurement data from the connected HomeWizard
        device. It uses the appropriate API version (v1 or v2) to fetch the
        measurement data and translates it into a dictionary format.

        Returns:
            dict: A dictionary containing the translated measurement data.
        """
        if self.connection:
            asyncio.run(self.connection.aget_measurement())
        else:
            raise ValueError("No connection to HomeWizard device established.")
        return self.connection.dev_measurement


if __name__ == "__main__":
    # Test the HomeWizard class
    test_serial = "5c2faf193aca"
    test_token = "your_token_goes_here"  # nosec B105:hardcoded_password_string
    hwe = MyHomeWizard(serial=test_serial, token=test_token, debug=True)
    print(json.dumps(hwe.target_device, indent=4))
    hwe.connect()
    print(hwe.get_measurement())
    print(hwe.api_version)
