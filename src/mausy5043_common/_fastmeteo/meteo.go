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
	Func string                 `json:"func"`
	Args map[string][]float64   `json:"args"`
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

		es := 611.2 * math.Exp(17.67*(temperature[i])/(kelvin-29.65))
		rvs := 0.622 * es / (pascal - es)
		rv := (humidity[i] / 100.0) * rvs
		qv := rv / (1.0 + rv)

		moistair := qv * rho * 1000.0 // g/m3

		out[i] = moistair
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

            result, err := moisture(temperature, humidity, pressure)
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
