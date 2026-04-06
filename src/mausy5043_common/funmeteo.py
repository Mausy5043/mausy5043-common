#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Provide various meteorological conversions."""

import numpy as np

Number = float | int
ArrayLike = Number | list[Number] | np.ndarray


def moisture(temperature: Number, relative_humidity: Number, pressure: Number) -> float:
    """Calculate moisture content of air given T, RH and P.

    Args:
        temperature: in degC
        relative_humidity: in %
        pressure: in mbara or hPa

    Returns:
        np.array: moisture content in kg/m3
    """
    kelvin: float = temperature + 273.15
    pascal: float = pressure
    rho: float = 2.8704 * kelvin / pascal

    svp: float = saturation_vapor_pressure(temperature)
    rvs: float = 0.622 * svp / (pascal - svp)
    rv: float = relative_humidity / 100.0 * rvs
    qv: float = rv / (1 + rv)
    moistair: float = qv * rho * 1000  # g water per m3 air
    return moistair


def wet_bulb_temperature(temperature: Number, relative_humidity: Number) -> float:
    """Calculate the wet bulb temperature of the air given T and RH.

    Args:
        temperature: in degC
        relative_humidity: in %

    Returns:
        Wet bulb temperature in degC
    """
    wbt: float = (
        temperature * np.arctan(0.151977 * np.sqrt(relative_humidity + 8.313659))
        + np.arctan(temperature + relative_humidity)
        - np.arctan(relative_humidity - 1.676331)
        + 0.00391838 * np.power(relative_humidity, 1.5) * np.arctan(0.023101 * relative_humidity)
        - 4.686035
    )
    return wbt


def saturation_vapor_pressure(temperature: Number) -> float:
    """Compute saturation vapor pressure (hPa) using Magnus formula.

    Args:
        temperature: temperature in °C (scalar or array)

    Returns:
        Saturation vapor pressure in hPa (scalar or numpy array)
    """
    kelvin: float = temperature + 273.15

    result = 6.112 * np.exp(17.67 * (kelvin - 273.15) / (kelvin - 29.65))
    return result


def dew_point_temperature(temperature: Number, relative_humidity: Number) -> float:
    """Compute dew point temperature (°C) from air temperature and relative humidity.

    Args:
        temperature: temperature in °C (scalar or array)
        relative_humidity: relative humidity in % (0–100, scalar or array)

    Returns:
        Dew point temperature in °C (scalar or numpy array)
    """

    svp: float = saturation_vapor_pressure(temperature)
    vp: float = (relative_humidity / 100.0) * svp  # actual vapor pressure
    ln_ratio = np.log(vp / 6.112)
    result = (243.5 * ln_ratio) / (17.67 - ln_ratio)
    return result


def relative_humidity_t2(T1: Number, RH1: Number, T2: Number) -> float:
    """Calculate new relative humidity after a temperature change.

    If T2 < dew point, RH2 = 100% (saturation).

    Args:
        T1: initial temperature in °C (scalar or array)
        RH1: initial relative humidity in % (scalar or array)
        T2: new temperature in °C (scalar or array)

    Returns:
        New relative humidity in % (scalar or numpy array)
    """

    # Actual vapor pressure at T1
    svp1 = saturation_vapor_pressure(T1)
    # Saturation vapor pressure at T2
    svp2 = saturation_vapor_pressure(T2)

    RH2 = RH1 * svp1 / svp2

    # Dew point check
    Td = dew_point_temperature(T1, RH1)

    # If T2 <= Td, air is saturated → RH = 100%
    if Td >= T2:
        RH2 = 100.0

    return RH2


if __name__ == "__main__":
    # Example usage with scalars
    T1: float = 23.0  # °C
    RH1: float = 73.0  # %
    P: float = 1013.0  # hPa

    Tm: float = moisture(T1, RH1, 1013)
    print(f"(Scalar) Moisture content:          {Tm:7.2f} kg/m3")
    Tw: float = wet_bulb_temperature(T1, RH1)
    print(f"(Scalar) Wet bulb temperature:      {Tw:7.2f} °C")
    Td: float = dew_point_temperature(T1, RH1)
    print(f"(Scalar) Dew point temperature:     {Td:7.2f} °C")
    Ps: float = saturation_vapor_pressure(T1)
    print(f"(Scalar) Saturation vapor pressure: {Ps:7.2f} hPa")

    T2: float = 17.95  # °C

    RH2 = float(relative_humidity_t2(T1, RH1, T2))
    print(f"(Scalar) New relative humidity:     {RH2:7.2f} %   (@ {T2} °C)")
    # Td = dew_point_temperature(T1, RH1)
    # Tm = moisture(T1, RH1, 1013)
    # Tw = wet_bulb_temperature(T1, RH1)

    # print(f"(Scalar) Dew point: {Td:.2f} °C")
    # print(f"(Scalar) Wetbulb T: {Tw:.2f} °C")
    # print(f"(Scalar) Moisture : {Tm[0]:.2f} kg/m3")
    # print(f"(Scalar) New relative humidity at {T2} °C: {RH2:.2f} %")
    # print(f"(Scalar) New dew point: {dew_point_temperature(T2, RH2):.2f} °C")
    # print(f"(Scalar) New wetbulb T: {wet_bulb_temperature(T2, RH2):.2f} °C")

    # # Example usage with arrays
    # T2_array = np.array([15.0, 20.0, 25.0, 30.0])
    # RH2_array = relative_humidity_t2(T1, RH1, T2_array)

    # print(f"(Array) New relative humidities at {T2_array} °C: {RH2_array}")
