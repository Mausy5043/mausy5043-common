#!/usr/bin/env python3

# wizwtr
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Discover Multi-cast devices that support Homewizard."""

import json
import logging.handlers
import os
import platform
import sys
import time
from typing import Any

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ZeroconfServiceTypes

# initialize logging
__is_macos: bool = platform.system() == "Darwin"
__hndlrs: list = []
if not __is_macos:
    hndlrs: list = [
        logging.handlers.SysLogHandler(
            address="/dev/log",
            facility=logging.handlers.SysLogHandler.LOG_DAEMON,
        ),
    ]
logging.basicConfig(
    level=logging.INFO,
    format="%(module)s.%(funcName)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=__hndlrs,
)
LOGGER: logging.Logger = logging.getLogger(__name__)

# fmt: off
# constants
DEBUG: bool = False
HERE: list = os.path.realpath(__file__).split("/")
MYID: str = HERE[-1]
MYAPP: str = HERE[-4]
MYROOT: str = "/".join(HERE[0:-4])
APPROOT: str = "/".join(HERE[0:-3])
NODE: str = os.uname()[1]

LOCAL_DIR: str = f"{os.getenv('HOME')}/.local"
DEVICE_FILE: str = f"{LOCAL_DIR}/devices.json"
# fmt: on


class ZcsListener(ServiceListener):
    r"""Overloaded class of zeroconf.ServiceListener.

    Examples of output:
    Service DABMAN i205 CDCCai6fu6g4c4ZZ._http._tcp.local. discovered
    ServiceInfo(type='_http._tcp.local.',
                name='DABMAN i205 CDCCai6fu6g4c4ZZ._http._tcp.local.',
                addresses=[b'\xc0\xa8\x02\x95'],
                port=80,
                weight=0,
                priority=0,
                server='http-DABMAN i205 CDCCai6fu6g4c4ZZ.local.',
                properties={b'path': b'/irdevice.xml,CUST_APP=0,BRAND=IMPERIAL,MAC=3475638B4984'},
                interface_index=None)
    ip = 192:168:2:149

    Service RBFILE._smb._tcp.local. discovered
    ServiceInfo(type='_smb._tcp.local.',
                name='RBFILE._smb._tcp.local.',
                addresses=[b'\xc0\xa8\x02\x12'],
                port=445,
                weight=0,
                priority=0,
                server='rbfile.local.',
                properties={b'': None},
                interface_index=None)
    ip = 192:168:2:18

    Service Canon_TS6251._http._tcp.local. discovered
    ServiceInfo(type='_http._tcp.local.',
                name='Canon_TS6251._http._tcp.local.',
                addresses=[b'\xc0\xa8\x02\xf0'],
                port=80,
                weight=0,
                priority=0,
                server='proton3.local.',
                properties={b'txtvers': b'1'},
                interface_index=None)
    ip = 192:168:2:240
    """

    def __init__(self) -> None:
        """Initialise the listener."""
        self.discovered: dict = {}

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Forget services that disappear during the discovery scan."""
        _name = name.replace(" ", "_")
        __name = _name.split(".")[0]
        LOGGER.debug(f"(  -) Service {__name} {type_} disappeared.")
        if __name in self.discovered:
            del self.discovered[__name]

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Overridden but not used."""
        _name = name.replace(" ", "_")
        __name = _name.split(".")[0]
        __type = type_.split(".")[0]
        LOGGER.debug(f"( * ) Service {__name} updated. ( {__type} )")
        # find out updated info about this device
        info = zc.get_service_info(type_, name)
        svc: str = ""
        prop: dict = {}
        if info:
            try:
                prop = self.debyte(info.properties)
                if info.addresses:
                    svc = ".".join(list(map(str, list(info.addresses[0]))))
            except BaseException:
                LOGGER.error(
                    f"Exception for device info: {info}\n {info.properties}\n {info.addresses}\n"
                )
                raise
        if (__name in self.discovered) and (__type in self.discovered[__name]):
            self.discovered[__name][__type] = {
                "ip": svc,
                "name": name,
                "type": type_,
                "properties": prop,
            }

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Remember services that are discovered during the scan."""
        _name = name.replace(" ", "_")
        __name = _name.split(".")[0]
        __type = type_.split(".")[0]
        # find out more about this device
        info = zc.get_service_info(type_, name)
        svc: str = ""
        prop: dict = {}
        if info:
            try:
                prop = self.debyte(info.properties)
                if info.addresses:
                    svc = ".".join(list(map(str, list(info.addresses[0]))))
            except BaseException:
                LOGGER.error(
                    f"Exception for device info: {info}\n {info.properties}\n {info.addresses}\n"
                )
                raise
        LOGGER.debug(f"(+  ) Service {__name} discovered ( {__type} ) on {svc}")
        # register the device
        if __name not in self.discovered:
            self.discovered[__name] = {
                f"{__type}": {
                    "ip": svc,
                    "name": name,
                    "type": type_,
                    "properties": prop,
                }
            }
        # additional services discovered for an already discovered device
        if __type not in self.discovered[__name]:
            self.discovered[__name][__type] = {
                "ip": svc,
                "name": name,
                "type": type_,
                "properties": prop,
            }

    @staticmethod
    def debyte(bytedict: Any) -> dict[str, str]:
        """Transform a dict of bytes to a dict of strings."""
        normdict = {}
        if bytedict:
            # bytedict may be empty or None
            for _y in bytedict:
                _x = bytedict[_y]
                # value None can't be decoded
                if _x:
                    normdict[_y.decode("ascii")] = _x.decode("ascii")
                else:
                    # protect against empty keys
                    if _y:
                        normdict[_y.decode("ascii")] = None
        return normdict


def save_discovery(disco_dict: dict) -> None:
    """Save the discovered services and info to a file."""
    LOGGER.debug("saving...")
    disco_str = json.dumps(disco_dict, indent=4, sort_keys=True)
    with open(DEVICE_FILE, "w", encoding="utf-8") as fp:
        fp.write(disco_str)


def discover_devices(search_time: float = 60.0) -> dict:
    """Discover services on the network using Zeroconf.

    This function uses the Zeroconf protocol to detect network services
    available within the local network. It initializes a Zeroconf instance
    and a listener, browses available service types, and collects
    information on discovered services over a fixed time period.

    The discovery process runs for 60 seconds, during which all
    network-discoverable services are identified and logged. The function
    returns a dictionary containing the details of all discovered services.

    Args:
        search_time (float): The time in seconds to search for services on
                             the network. The default value is 60.0.

    Returns:
        dict: A dictionary containing the discovered services and their details.

    Raises: Nothing
    """
    _zc = Zeroconf()
    _ls = ZcsListener()
    service_list = ZeroconfServiceTypes.find()
    browsers = []
    for _service in service_list:
        LOGGER.debug(f"(   ) Listening for service: {_service}")
        browsers.append(ServiceBrowser(_zc, _service, _ls))

    t0: float = time.time()
    dt: float = 0.0
    while dt < search_time:
        dt = time.time() - t0

    _zc.close()

    if DEBUG:
        save_discovery(_ls.discovered)
    return _ls.discovered


def get_ip(service: str, filtr: str = '', timeout: float = 60.0) -> list[str]:
    """Discover and retrieve IP addresses for a given service.

    Args:
        service (str): The name of the service to discover.
        filtr (str): A filter string to match specific services.
        timeout (float): The maximum time in seconds to wait for the discovery to complete.

    Returns:
        list[str]: A list of IP addresses that match the given service and filter.
    """
    _ip: list[str] = []
    _devices: dict = discover_devices(search_time=timeout)
    LOGGER.debug("Discovery done.")
    LOGGER.debug(f"Found {len(_devices)} devices in total. Pruning and filtering...")
    _devices = prune_services(_devices, [service])
    if filtr:
        _devices = filter_properties(_devices, service, filtr)
    for _d in _devices:
        _ip.append(_devices[_d][service]["ip"])
    return _ip


def prune_services(devices: dict, services: list[str]) -> dict:
    """Remove devices that do not provide a specific service."""
    LOGGER.debug(f"Looking for devices providing '{services}'")
    for device in list(devices.keys()):
        if not any(service in devices[device] for service in services):
            del devices[device]
    return devices


def filter_properties(devices: dict, service: str, filtr: str) -> dict:
    """Filter devices based on property contents."""
    devices_to_remove = []
    LOGGER.debug(f"Looking for devices matching '{filtr}' in {service}")
    for device, services in devices.items():
        for service_type, service_data in services.items():
            if service_type == service:
                # Check if any property contains the filter; exit early if found
                if any(filtr in value for value in service_data["properties"].values()):
                    LOGGER.debug(f"Found {filtr} in {device} with IP {service_data['ip']}")
                    break
                else:
                    # Mark the device for removal if filter not found
                    devices_to_remove.append(device)
                    break

    # Remove marked devices
    for device in devices_to_remove:
        del devices[device]

    return devices


if __name__ == "__main__":
    # initialise logging to console
    DEBUG = True
    LOGGER.addHandler(logging.StreamHandler(sys.stdout))
    LOGGER.level = logging.DEBUG

    LOGGER.debug("Debug-mode started.")
    LOGGER.debug(f"IP = {get_ip(service='_homewizard', filtr='HWE-P1')}")
    # print(json.dumps(discover_devices(), indent=4, sort_keys=True))
    LOGGER.debug("...done")
