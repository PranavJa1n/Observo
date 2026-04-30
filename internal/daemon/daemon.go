package daemon

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"syscall"

	"github.com/PranavJa1n/Observo/internal/config"
)

// IsRunning checks if the daemon is currently running
// Returns true if PID file exists and process is alive
func IsRunning() (bool, error) {
	pid, err := GetPID()
	if err != nil {
		return false, nil // No PID file = not running
	}

	if runtime.GOOS == "windows" {
		// On Windows, Signal(0) is not supported.
		// Use tasklist to check if the process is alive by PID.
		out, err := exec.Command("tasklist", "/FI", fmt.Sprintf("PID eq %d", pid), "/NH").Output()
		if err != nil {
			RemovePID()
			return false, nil
		}
		if !strings.Contains(string(out), fmt.Sprintf("%d", pid)) {
			RemovePID() // Clean up stale PID file
			return false, nil
		}
		return true, nil
	}

	// Unix: use Signal(0) to check if process is alive
	process, err := os.FindProcess(pid)
	if err != nil {
		return false, nil
	}
	err = process.Signal(syscall.Signal(0))
	if err != nil {
		RemovePID()
		return false, nil
	}

	return true, nil
}

// GetPID reads the PID from the PID file
// Returns error if file doesn't exist or contains invalid data
func GetPID() (int, error) {
	pidPath := config.GetPIDPath()

	data, err := os.ReadFile(pidPath)
	if err != nil {
		return 0, err
	}

	pid, err := strconv.Atoi(strings.TrimSpace(string(data)))
	if err != nil {
		return 0, fmt.Errorf("invalid PID in file: %v", err)
	}

	return pid, nil
}

// WritePID writes the PID to the PID file
func WritePID(pid int) error {
	pidPath := config.GetPIDPath()

	// Ensure directory exists
	observoDir := config.GetObservoDir()
	if err := os.MkdirAll(observoDir, 0755); err != nil {
		return err
	}

	return os.WriteFile(pidPath, []byte(fmt.Sprintf("%d", pid)), 0644)
}

// RemovePID deletes the PID file
func RemovePID() error {
	pidPath := config.GetPIDPath()
	return os.Remove(pidPath)
}

// StartDaemon starts Observo in daemon mode (background process)
// It forks the current process and runs it in the background
func StartDaemon() error {
	// Check if already running
	running, err := IsRunning()
	if err != nil {
		return err
	}
	if running {
		return fmt.Errorf("daemon is already running")
	}

	// Get the path to the current executable
	executable, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %v", err)
	}

	// Prepare command to run in background
	// We'll run the same binary with a special flag to indicate daemon mode
	cmd := exec.Command(executable, "start", "--foreground")

	// Redirect stdout and stderr to log file
	logPath := config.GetLogPath()
	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return fmt.Errorf("failed to open log file: %v", err)
	}

	cmd.Stdout = logFile
	cmd.Stderr = logFile

	// Detach from current process (platform-specific)
	// Note: Windows doesn't need special handling here
	// The process will run in background automatically when parent exits

	// Start the process
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start daemon: %v", err)
	}

	// Write PID file
	if err := WritePID(cmd.Process.Pid); err != nil {
		cmd.Process.Kill() // Kill the process if we can't write PID
		return fmt.Errorf("failed to write PID file: %v", err)
	}

	// Release the process (don't wait for it)
	cmd.Process.Release()

	fmt.Printf("✅ Daemon started with PID %d\n", cmd.Process.Pid)
	fmt.Printf("📝 Logs: %s\n", logPath)

	return nil
}

// StopDaemon stops the running daemon
// Reads PID from file and sends kill signal
func StopDaemon() error {
	// Check if running
	running, err := IsRunning()
	if err != nil {
		return err
	}
	if !running {
		return fmt.Errorf("daemon is not running")
	}

	// Get PID
	pid, err := GetPID()
	if err != nil {
		return err
	}

	// Find process
	process, err := os.FindProcess(pid)
	if err != nil {
		return fmt.Errorf("failed to find process: %v", err)
	}

	// Send kill signal
	// On Unix: SIGTERM
	// On Windows: TerminateProcess
	if err := process.Kill(); err != nil {
		return fmt.Errorf("failed to kill process: %v", err)
	}

	// Remove PID file
	if err := RemovePID(); err != nil {
		return fmt.Errorf("daemon stopped but failed to remove PID file: %v", err)
	}

	fmt.Printf("✅ Daemon stopped (PID %d)\n", pid)
	return nil
}
