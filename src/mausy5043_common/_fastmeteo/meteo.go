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

func moisture(temperature, humidity, pressure []float64) ([]float64, error) {
	n := len(temperature)

	if len(humidity) != n || len(pressure) != n {
		return nil, fmt.Errorf("input arrays must have equal length")
	}

	out := make([]float64, n)

	for i := range n {
		kelvin := temperature[i] + 273.15
		pascal := pressure[i] * 100.0

		rho := (287.04 * kelvin) / pascal

		es := a_saturation_vapor_pressure(temperature[i])
		rvs := 0.622 * es / (pascal - es)
		rv := (humidity[i] / 100.0) * rvs
		qv := rv / (1.0 + rv)

		moistair := qv * rho * 1000.0 // g/m3

		out[i] = moistair
	}

	return out, nil
}

func a_saturation_vapor_pressure(temperature float64) float64 {
	// Use the Magnus formula for saturation vapor pressure over liquid water
	// to calculate the saturation vapor pressure at a given temperature.
	// T in °C
	// returns pressure in Pa
	kelvin := temperature + 273.15
	es := 611.2 * math.Exp(17.67*(temperature)/(kelvin-29.65)) // Pa
	return es
}

func saturation_vapor_pressure(temperature []float64) ([]float64, error) {
	n := len(temperature)

	out := make([]float64, n)

	for i := range n {
		es := a_saturation_vapor_pressure(temperature[i])
		out[i] = es // Pa
	}
	return out, nil
}

func wetBulbTemperature(temperature, relativeHumidity float64) float64 {
	// Calculate the wet bulb temperature of the air given T and RH.
	// temperature: in degC
	// relativeHumidity: in %
	// Returns: Wet bulb temperature in degC
	wbt := (temperature*math.Atan(0.151977*math.Sqrt(relativeHumidity+8.313659)) +
		math.Atan(temperature+relativeHumidity) -
		math.Atan(relativeHumidity-1.676331) +
		0.00391838*math.Pow(relativeHumidity, 1.5)*math.Atan(0.023101*relativeHumidity) -
		4.686035)
	return wbt
}

/*
func relative_humidity_t2(temperature1, humidity1, temperature2 []float64) ([]float64, error) {
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
        es1 := saturation_vapor_pressure(T1)
        e_actual := (RH1 / 100.0) * es1

        // Dew point check
        Td := dew_point_temperature(T1, RH1)

        // Saturation vapor pressure at T2
        es2 := saturation_vapor_pressure(T2)

        // Compute RH2
        RH2 := (e_actual / es2) * 100.0

        // If T2 <= Td, air is saturated → RH = 100%
        //RH2 = np.where(Td >= T2, 100.0, RH2)

		out[i] = RH2
	}

	return out, nil
}
*/

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
		result, err := moisture(temperature, humidity, pressure)
		if err != nil {
			respondError(err)
			return
		}
		respondOK(result)

	case "saturation_vapour_pressure":
		temperature := req.Args["temperature"]
		result, err := saturation_vapor_pressure(temperature)
		if err != nil {
			respondError(err)
			return
		}
		respondOK(result)

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
