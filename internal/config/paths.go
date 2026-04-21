package config

import (
	"os"
	"path/filepath"
)

func GetObservoDir() string { // function for getting the main directory of the observo
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".observo")
}

func GetConfigPath() string { // function for getting the path of the config file
	return filepath.Join(GetObservoDir(), "config.json")
}

func GetDBPath() string { // function for getting the path of the sqlitee db file
	return filepath.Join(GetObservoDir(), "observo.db")
}

func GetPIDPath() string { // function for getting the path of the PID file (for daemon mode)
	return filepath.Join(GetObservoDir(), "observo.pid")
}

func GetLogPath() string { // function for getting the path of the daemon log file
	return filepath.Join(GetObservoDir(), "observo.log")
}
