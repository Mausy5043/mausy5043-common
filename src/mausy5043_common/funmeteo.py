#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Provide various meteorological conversions."""

import numpy as np

Number = float | int
ArrayLike = Number | np.ndarray


def moisture(temperature: Number, relative_humidity: Number, pressure: Number) -> np.ndarray:
    """Calculate moisture content of air given T, RH and P.

    Args:
        temperature: in degC
        relative_humidity: in %
        pressure: in mbara or hPa

    Returns:
        np.array: moisture content in kg/m3
    """
    kelvin: float = temperature + 273.15
    pascal: float = pressure * 100
    rho: float = (287.04 * kelvin) / pascal

    es: float = 611.2 * np.exp(17.67 * (kelvin - 273.15) / (kelvin - 29.65))
    rvs: float = 0.622 * es / (pascal - es)
    rv: float = relative_humidity / 100.0 * rvs
    qv: float = rv / (1 + rv)
    moistair: float = qv * rho * 1000  # g water per m3 air
    return np.array([moistair])


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


def saturation_vapor_pressure(temperature: ArrayLike) -> ArrayLike:
    """Compute saturation vapor pressure (hPa) using Magnus formula.

    Args:
        temperature: temperature in °C (scalar or array)

    Returns:
        Saturation vapor pressure in hPa (scalar or numpy array)
    """
    scalar_input = np.isscalar(temperature)
    _T = np.asarray(temperature, dtype=float)
    result = 6.112 * np.exp((17.67 * _T) / (_T + 243.5))
    return result.item() if scalar_input else result


def dew_point_temperature(temperature: ArrayLike, relative_humidity: ArrayLike) -> ArrayLike:
    """Compute dew point temperature (°C) from air temperature and relative humidity.

    Args:
        temperature: temperature in °C (scalar or array)
        relative_humidity: relative humidity in % (0–100, scalar or array)

    Returns:
        Dew point temperature in °C (scalar or numpy array)
    """
    scalar_input = np.isscalar(temperature) and np.isscalar(relative_humidity)
    _T = np.asarray(temperature, dtype=float)
    _RH = np.asarray(relative_humidity, dtype=float)

    es = saturation_vapor_pressure(_T)
    e = (_RH / 100.0) * es  # actual vapor pressure
    ln_ratio = np.log(e / 6.112)
    result = (243.5 * ln_ratio) / (17.67 - ln_ratio)
    return result.item() if scalar_input else result


def relative_humidity_t2(T1: ArrayLike, RH1: ArrayLike, T2: ArrayLike) -> ArrayLike:
    """Calculate new relative humidity after a temperature change.

    If T2 < dew point, RH2 = 100% (saturation).

    Args:
        T1: initial temperature in °C (scalar or array)
        RH1: initial relative humidity in % (scalar or array)
        T2: new temperature in °C (scalar or array)

    Returns:
        New relative humidity in % (scalar or numpy array)
    """
    scalar_input = np.isscalar(T1) and np.isscalar(RH1) and np.isscalar(T2)
    T1 = np.asarray(T1, dtype=float)
    RH1 = np.asarray(RH1, dtype=float)
    T2 = np.asarray(T2, dtype=float)

    # Actual vapor pressure at T1
    es1 = saturation_vapor_pressure(T1)
    e_actual = (RH1 / 100.0) * es1

    # Dew point check
    Td = dew_point_temperature(T1, RH1)

    # Saturation vapor pressure at T2
    es2 = saturation_vapor_pressure(T2)

    # Compute RH2
    RH2 = (e_actual / es2) * 100.0

    # If T2 <= Td, air is saturated → RH = 100%
    RH2 = np.where(Td >= T2, 100.0, RH2)

    return RH2.item() if scalar_input else RH2


# Example usage with scalars
T1: float = 17.0  # °C
RH1: float = 73.0  # %
T2: float = 21.0  # °C

RH2 = float(relative_humidity_t2(T1, RH1, T2))
Td = dew_point_temperature(T1, RH1)
Tm = moisture(T1, RH1, 1013)
Tw = wet_bulb_temperature(T1, RH1)

print(f"(Scalar) Dew point: {Td:.2f} °C")
print(f"(Scalar) Wetbulb T: {Tw:.2f} °C")
print(f"(Scalar) Moisture : {Tm[0]:.2f} kg/m3")
print(f"(Scalar) New relative humidity at {T2} °C: {RH2:.2f}%")
print(f"(Scalar) New dew point: {dew_point_temperature(T2, RH2):.2f} °C")
print(f"(Scalar) New wetbulb T: {wet_bulb_temperature(T2, RH2):.2f} °C")

# Example usage with arrays
T2_array = np.array([15.0, 20.0, 25.0, 30.0])
RH2_array = relative_humidity_t2(T1, RH1, T2_array)

print(f"(Array) New relative humidities at {T2_array} °C: {RH2_array}")
