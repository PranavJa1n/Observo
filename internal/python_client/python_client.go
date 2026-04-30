package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type PythonClient struct { // used to send logs to the python service
	baseURL string // URL where python is running
	aiModel string // the AI model to use
	client  *http.Client
}

type AnalysisResult struct {
	RootCause          string   `json:"root_cause"`
	Severity           string   `json:"severity"`
	Recommendations    []string `json:"recommendations"`
	AffectedComponents []string `json:"affected_components"`
	Timestamp          string   `json:"timestamp"`
	Summary            string   `json:"summary"`
}

type ProcessResponse struct {
	Status    string          `json:"status"`
	Total     int             `json:"total"`
	GoodCount int             `json:"good_count"`
	BadCount  int             `json:"bad_count"`
	Analysis  *AnalysisResult `json:"analysis"`
	Message   string          `json:"message"`
}

func New(baseURL string, aiModel string) *PythonClient { // function for creating new python client
	return &PythonClient{
		baseURL: baseURL,
		aiModel: aiModel,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *PythonClient) SendBatch(logs []string) (*ProcessResponse, error) { // function to send a batch of logs to the python service
	if len(logs) == 0 { // Nothing must be send if there are no logs
		return nil, nil
	}

	payload := map[string]interface{}{ // interface can take any value
		"logs":  logs,
		"model": c.aiModel,
	}

	jsonData, err := json.Marshal(payload) // converting payload to JSON
	if err != nil {
		return nil, fmt.Errorf("failed to marshal JSON: %v", err)
	}

	url := c.baseURL + "/process" // /process is the route in the python service which will recieve the batch of the logs
	resp, err := c.client.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to send batch: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK { // Checking if the send request is having status ok or nots
		return nil, fmt.Errorf("Python service returned error: %d", resp.StatusCode)
	}

	var processResp ProcessResponse
	if err := json.NewDecoder(resp.Body).Decode(&processResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	fmt.Printf("✅ Sent %d logs to Python service\n", len(logs))
	return &processResp, nil
}

func (c *PythonClient) HealthCheck() error { // function for checking if python service is running or not
	url := c.baseURL + "/health"
	resp, err := c.client.Get(url)
	if err != nil {
		return fmt.Errorf("Python service not reachable: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Python service unhealthy: %d", resp.StatusCode)
	}

	return nil
}

func (c *PythonClient) WaitForPython(maxWait time.Duration) error {
	fmt.Println("Waiting for Python service")

	timeout := time.After(maxWait)
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for { // loop that will keep on trying to find the python service until and unless some case is matched that is if go service is timeout or python service is found
		select {
		case <-timeout:
			return fmt.Errorf("Python service not FOUND")

		case <-ticker.C:
			err := c.HealthCheck()
			if err == nil {
				fmt.Println("Python service FOUND!!")
				return nil
			}
		}
	}
}
