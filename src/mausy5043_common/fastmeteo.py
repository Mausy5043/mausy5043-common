#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2026  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Provide various meteorological conversions faster."""

import json
import platform
import subprocess
from pathlib import Path

import numpy as np

Number = float | int
ArrayLike = Number | np.ndarray


# --- Binary resolution -------------------------------------------------------


def _get_binary_path() -> Path:
    base = Path(__file__).parent / "_fastmeteo" / "bin"

    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize platform names
    if system == "darwin":
        system = "darwin"
    elif system == "linux":
        system = "linux"
    elif system == "windows":
        system = "windows"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    # Normalize architecture
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    name = f"meteo-{system}-{arch}"
    if system == "windows":
        name += ".exe"

    binary = base / name

    if not binary.exists():
        raise RuntimeError(f"Missing fastmeteo binary: {binary}")

    return binary


# --- Core call helper --------------------------------------------------------


def _normalize_inputs(*args: ArrayLike) -> tuple[list[np.ndarray], tuple[int, ...]]:
    """Normalize input arguments for Go processing.

    This function:
    - Converts all inputs to NumPy arrays of dtype float
    - Applies NumPy broadcasting so all inputs share the same shape
    - Flattens each array to 1D for efficient transfer to the Go backend
    - Returns the flattened arrays along with the original broadcast shape

    Args:
        *args: Scalars or NumPy arrays representing input variables

    Returns:
        A tuple containing:
        - List of 1D NumPy arrays (all of equal length)
        - The original broadcasted shape (used to reshape the result)

    Example:
        >>> _normalize_inputs(np.array([10, 20]), 50, 1013)
        ([array([10., 20.]), array([50., 50.]), array([1013., 1013.])], (2,))
    """
    arrays = [np.asarray(a, dtype=float) for a in args]
    broadcasted = np.broadcast_arrays(*arrays)
    return [a.ravel() for a in broadcasted], broadcasted[0].shape


def _call_go(func: str, **kwargs) -> np.ndarray:
    """Call the Go backend to execute a meteorological function.

    This function:
    - Normalizes and broadcasts all input arguments using NumPy
    - Flattens inputs to 1D arrays for efficient processing in Go
    - Serializes the request to JSON and sends it to the Go binary via stdin
    - Parses the JSON response from stdout
    - Converts the result back into a NumPy array and reshapes it to match input

    Args:
        func: Name of the function to execute in the Go backend
        **kwargs: Input arguments (scalars or NumPy arrays)

    Returns:
        A NumPy array containing the computed results, matching the broadcasted input shape

    Raises:
        RuntimeError: If the Go process fails or returns an error
        json.JSONDecodeError: If the Go output is not valid JSON

    Example:
        >>> _call_go("moisture", temp=[10, 20], humidity=50, pressure=1013)
        array([0.007, 0.014])
    """
    binary = _get_binary_path()

    keys = list(kwargs.keys())
    values = list(kwargs.values())

    arrays, shape = _normalize_inputs(*values)

    payload = {
        "func": func,
        "args": dict(zip(keys, [a.tolist() for a in arrays], strict=True)),
    }

    result = subprocess.run(
        [str(binary)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    response = json.loads(result.stdout)

    if "error" in response:
        raise RuntimeError(response["error"])

    out = np.array(response["result"], dtype=float)
    return out  # .reshape(shape)


# --- Public API (mirror funmeteo.py) -----------------------------------------


def moisture(temperature: Number, relative_humidity: Number, pressure: Number) -> np.ndarray:
    """Calculate moisture content of air given T, RH and P.

    Args:
        temperature: in degC
        relative_humidity: in %
        pressure: in mbara or hPa

    Returns:
        np.array: moisture content in kg/m3
    """
    return _call_go(
        "moisture", temperature=temperature, humidity=relative_humidity, pressure=pressure
    )


if __name__ == "__main__":
    # Example usage with scalars
    T1: float = 17.0  # °C
    RH1: float = 73.0  # %
    T2: float = 21.0  # °C

    # RH2 = float(relative_humidity_t2(T1, RH1, T2))
    # Td = dew_point_temperature(T1, RH1)
    Tm = moisture(T1, RH1, 1013)
    # Tw = wet_bulb_temperature(T1, RH1)

    # print(f"(Scalar) Dew point: {Td:.2f} °C")
    # print(f"(Scalar) Wetbulb T: {Tw:.2f} °C")
    print(f"(Scalar) Moisture : {Tm[0]:.2f} kg/m3")
    # print(f"(Scalar) New relative humidity at {T2} °C: {RH2:.2f} %")
    # print(f"(Scalar) New dew point: {dew_point_temperature(T2, RH2):.2f} °C")
    # print(f"(Scalar) New wetbulb T: {wet_bulb_temperature(T2, RH2):.2f} °C")

    # Example usage with arrays
    # T2_array = np.array([15.0, 20.0, 25.0, 30.0])
    # RH2_array = relative_humidity_t2(T1, RH1, T2_array)

    # print(f"(Array) New relative humidities at {T2_array} °C: {RH2_array}")
