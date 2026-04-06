package main

import (
	"encoding/json"
	"fmt"
	"io"
	"math"
	"os"
)

// --- Request/Response structs -----------------------------------------------

type Request struct {
	Func string               `json:"func"`
	Args map[string][]float64 `json:"args"`
}

type Response struct {
	Result []float64 `json:"result,omitempty"`
	Error  string    `json:"error,omitempty"`
}

// --- Core calculation --------------------------------------------------------

func Moisture(temperature, humidity, pressure []float64) ([]float64, error) {
	n := len(temperature)

	if len(humidity) != n || len(pressure) != n {
		return nil, fmt.Errorf("input arrays must have equal length")
	}

	out := make([]float64, n)

	for i := range n {
		kelvin := temperature[i] + 273.15
		pascal := pressure[i] * 100.0

		rho := (287.04 * kelvin) / pascal

		es := a_Saturation_Vapor_Pressure(temperature[i])
		rvs := 0.622 * es / (pascal - es)
		rv := (humidity[i] / 100.0) * rvs
		qv := rv / (1.0 + rv)

		moistair := qv * rho * 1000.0 // g/m3

		out[i] = moistair
	}

	return out, nil
}

func a_Saturation_Vapor_Pressure(temperature float64) float64 {
	// Use the Magnus formula for saturation vapor pressure over liquid water
	// to calculate the saturation vapor pressure at a given temperature.
	// T in °C
	// returns pressure in Pa
	kelvin := temperature + 273.15
	es := 611.2 * math.Exp(17.67*(temperature)/(kelvin-29.65)) // Pa
	return es
}

func Saturation_Vapor_Pressure(temperature []float64) ([]float64, error) {
    // returns saturation vapor pressure in hPa
	n := len(temperature)

	out := make([]float64, n)

	for i := range n {
		es := a_Saturation_Vapor_Pressure(temperature[i])
		out[i] = es / 100.0 // hPa
	}
	return out, nil
}

func Wet_Bulb_Temperature(temperature, humidity []float64) ([]float64, error) {
	// Calculate the wet bulb temperature of the air given T and RH.
	// temperature: in degC
	// humidity: in %
	// Returns: Wet bulb temperature in degC
	n := len(temperature)

	if len(humidity) != n || len(temperature) != n {
		return nil, fmt.Errorf("input arrays must have equal length")
	}

	out := make([]float64, n)

	for i := range n {
	    T := temperature[i]
		RH := humidity[i]
		wbt := (T*
			math.Atan(0.151977 * math.Sqrt(RH + 8.313659)) +
			math.Atan(T + RH) -
			math.Atan(RH - 1.676331) +
			0.00391838*math.Pow(RH, 1.5)*math.Atan(0.023101 * RH) -
			4.686035)
		out[i] = wbt
	}
	return out, nil
}

func Dew_Point_Temperature(temperature, humidity []float64) ([]float64, error) {
    // Compute dew point temperature (°C) from air temperature and relative humidity.
    //     temperature: temperature in °C
    //     relative_humidity: relative humidity in % (0–100)
    // Returns:
    //     Dew point temperature in °C
   	n := len(temperature)

	if len(humidity) != n {
		return nil, fmt.Errorf("input arrays must have equal length")
	}

	out := make([]float64, n)

	for i := range n {
	    svp:= a_Saturation_Vapor_Pressure(temperature[i]) / 100
		vp:= svp * (humidity[i] / 100.0)
		ln_ratio := math.Log(vp / 6.112)
		dpt := (243.5 * ln_ratio) / (17.67 - ln_ratio)
		out[i] = dpt
	}
	return out, nil
}

func Relative_Humidity_T2(temperature1, humidity1, temperature2 []float64) ([]float64, error) {
	n := len(temperature1)

	if len(humidity1) != n || len(temperature2) != n {
		return nil, fmt.Errorf("input arrays must have equal length")
	}

	out := make([]float64, n)

	for i := range n {
        T1 := temperature1[i]
        RH1 := humidity1[i]
        T2 := temperature2[i]

        // Actual vapor pressure at T1
        es1 := a_Saturation_Vapor_Pressure(T1)
        e_actual := (RH1 / 100.0) * es1

        // Dew point check
        // Td := dew_point_temperature(T1, RH1)

        // Saturation vapor pressure at T2
        es2 := a_Saturation_Vapor_Pressure(T2)

        // Compute RH2
        RH2 := (e_actual / es2) * 100.0

        // If T2 <= Td, air is saturated → RH = 100%
        //RH2 = np.where(Td >= T2, 100.0, RH2)

		out[i] = RH2
	}

	return out, nil
}


// --- Main dispatcher ---------------------------------------------------------

func main() {
	// Read stdin
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		respondError(err)
		return
	}

	var req Request
	if err := json.Unmarshal(input, &req); err != nil {
		respondError(err)
		return
	}

	switch req.Func {

	case "moisture":
		temperature := req.Args["temperature"]
		humidity := req.Args["humidity"]
		pressure := req.Args["pressure"]
		// println("Received moisture request with temperature:", temperature, "humidity:", humidity, "pressure:", pressure)
		result, err := Moisture(temperature, humidity, pressure)
		if err != nil {
			respondError(err)
			return
		}
		respondOK(result)

	case "saturation_vapour_pressure":
		temperature := req.Args["temperature"]
		result, err := Saturation_Vapor_Pressure(temperature)
		if err != nil {
			respondError(err)
			return
		}
		respondOK(result)

	case "wet_bulb_temperature":
    	temperature := req.Args["temperature"]
    	humidity := req.Args["humidity"]
		result, err := Wet_Bulb_Temperature(temperature, humidity)
		if err != nil {
			respondError(err)
			return
		}
		respondOK(result)

	case "dew_point_temperature":
    	temperature := req.Args["temperature"]
    	humidity := req.Args["humidity"]
				result, err := Dew_Point_Temperature(temperature, humidity)
				if err != nil {
					respondError(err)
					return
				}
				respondOK(result)

	// case "relative_humidity_t2":
	// 	temperature1 := req.Args["temperature1"]
	// 	humidity1 := req.Args["humidity_t1"]
	// 	temperature2 := req.Args["temperature2"]
	// 	// println("Received moisture request with temperature:", temperature, "humidity:", humidity, "pressure:", pressure)
	// 	result, err := relative_humidity_t2(temperature1, humidity1, temperature2)
	// 	if err != nil {
	// 		respondError(err)
	// 		return
	// 	}

	default:
		respondError(fmt.Errorf("unknown function: %s", req.Func))
	}
}

// --- Helpers -----------------------------------------------------------------

func respondOK(result []float64) {
	resp := Response{Result: result}
	enc := json.NewEncoder(os.Stdout)
	_ = enc.Encode(resp)
}

func respondError(err error) {
	resp := Response{Error: err.Error()}
	enc := json.NewEncoder(os.Stdout)
	_ = enc.Encode(resp)
}
