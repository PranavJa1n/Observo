package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
)

type Config struct { // holds all the config of the observo
	Source     string `json:"source"` // Always "local" for now
	Path       string `json:"path"`   // directory from where we have to observe the logs
	AlertEmail string `json:"alert_email"`
	APIKey     string `json:"api_key"`
}

func Load() (*Config, error) {
	configPath := GetConfigPath()

	if _, err := os.Stat(configPath); os.IsNotExist(err) { // checking if config file exist or not
		return nil, errors.New("config not found - run 'observo init' first")
	}

	data, err := os.ReadFile(configPath) // reading the config file
	if err != nil {
		return nil, err
	}

	var cfg Config
	err = json.Unmarshal(data, &cfg) // parsing the config data into the Config struct
	if err != nil {
		return nil, err
	}

	return &cfg, nil
}

func (c *Config) Save() error { // writes the config to the ~/.observo/config.json
	observoDir := GetObservoDir() // make sure that directory exists
	err := os.MkdirAll(observoDir, 0755)
	if err != nil {
		return err
	}

	data, err := json.MarshalIndent(c, "", "  ") // config to JSON
	if err != nil {
		return err
	}

	configPath := GetConfigPath()
	err = os.WriteFile(configPath, data, 0644) // writting to the file
	if err != nil {
		return err
	}

	return nil
}

func (c *Config) Validate() error { // fuction checks if the values in the config are valid or not

	if c.Path == "" { // checking if the path for the logs is empty or not
		return errors.New("log path cannot be empty")
	}

	if _, err := os.Stat(c.Path); os.IsNotExist(err) { // checking if the path for the logs exist or not
		return fmt.Errorf("log path does not exist: %s", c.Path)
	}

	if c.APIKey == "" {
		return errors.New("API key cannot be empty") // if api is empty or not
	}

	if c.AlertEmail != "" && !strings.Contains(c.AlertEmail, "@") { // email is optional but still giving it a basic check for the @ sign
		return errors.New("invalid email format")
	}

	return nil
}
