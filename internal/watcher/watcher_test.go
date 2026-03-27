package watcher

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNew(t *testing.T) {
	logPath := "/tmp/test.log"
	watcher := New(logPath)

	if watcher == nil {
		t.Fatal("New() returned nil")
	}

	if watcher.logPath != logPath {
		t.Errorf("Expected logPath %s, got %s", logPath, watcher.logPath)
	}

	if watcher.logChan == nil {
		t.Error("logChan should not be nil")
	}

	if watcher.stopChan == nil {
		t.Error("stopChan should not be nil")
	}

	if watcher.lastSize != 0 {
		t.Errorf("Expected lastSize 0, got %d", watcher.lastSize)
	}
}

func TestLogChan(t *testing.T) {
	watcher := New("/tmp/test.log")
	logChan := watcher.LogChan()

	if logChan == nil {
		t.Error("LogChan() returned nil")
	}

	// Verify it's the same channel
	testMsg := "test log"
	go func() {
		watcher.logChan <- testMsg
	}()

	select {
	case msg := <-logChan:
		if msg != testMsg {
			t.Errorf("Expected '%s', got '%s'", testMsg, msg)
		}
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for log message")
	}
}

func TestStartWithNonExistentFile(t *testing.T) {
	watcher := New("/nonexistent/path/to/file.log")

	done := make(chan error)
	go func() {
		done <- watcher.Start()
	}()

	// Should return error for nonexistent file
	select {
	case err := <-done:
		if err == nil {
			t.Error("Expected error for nonexistent file, got nil")
		}
	case <-time.After(2 * time.Second):
		watcher.Stop()
		t.Fatal("Timeout - Start() should fail quickly for nonexistent file")
	}
}

func TestStartAndStop(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}
	f.Close()

	watcher := New(logFile)

	// Start watcher
	done := make(chan error)
	go func() {
		done <- watcher.Start()
	}()

	// Give it time to start
	time.Sleep(100 * time.Millisecond)

	// Stop watcher
	watcher.Stop()

	// Should return from Start()
	select {
	case err := <-done:
		if err != nil {
			t.Errorf("Start() returned error after Stop(): %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Start() did not return after Stop()")
	}
}

func TestReadNewLines(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}

	// Write initial content
	initialLogs := []string{"Log line 1", "Log line 2"}
	for _, log := range initialLogs {
		f.WriteString(log + "\n")
	}
	f.Close()

	watcher := New(logFile)

	// Start watcher
	go watcher.Start()
	defer watcher.Stop()

	// Give watcher time to initialize
	time.Sleep(200 * time.Millisecond)

	// Write new logs
	f, err = os.OpenFile(logFile, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		t.Fatalf("Failed to open log file: %v", err)
	}

	newLogs := []string{"New log 1", "New log 2", "New log 3"}
	for _, log := range newLogs {
		f.WriteString(log + "\n")
	}
	f.Close()

	// Collect logs from channel
	receivedLogs := make([]string, 0)
	timeout := time.After(2 * time.Second)

collectLoop:
	for i := 0; i < len(newLogs); i++ {
		select {
		case log := <-watcher.LogChan():
			receivedLogs = append(receivedLogs, log)
		case <-timeout:
			break collectLoop
		}
	}

	if len(receivedLogs) != len(newLogs) {
		t.Errorf("Expected %d logs, got %d", len(newLogs), len(receivedLogs))
	}

	for i, expected := range newLogs {
		if i >= len(receivedLogs) {
			t.Errorf("Missing log at index %d: expected '%s'", i, expected)
			continue
		}
		if receivedLogs[i] != expected {
			t.Errorf("Log at index %d: expected '%s', got '%s'", i, expected, receivedLogs[i])
		}
	}
}

func TestWatcherIgnoresEmptyLines(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}
	f.Close()

	watcher := New(logFile)

	// Start watcher
	go watcher.Start()
	defer watcher.Stop()

	// Give watcher time to initialize
	time.Sleep(200 * time.Millisecond)

	// Write logs with empty lines
	f, err = os.OpenFile(logFile, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		t.Fatalf("Failed to open log file: %v", err)
	}

	f.WriteString("Log 1\n")
	f.WriteString("\n")
	f.WriteString("Log 2\n")
	f.WriteString("\n")
	f.WriteString("\n")
	f.WriteString("Log 3\n")
	f.Close()

	// Collect logs
	receivedLogs := make([]string, 0)
	timeout := time.After(2 * time.Second)

collectLoop:
	for {
		select {
		case log := <-watcher.LogChan():
			receivedLogs = append(receivedLogs, log)
			if len(receivedLogs) >= 3 {
				break collectLoop
			}
		case <-timeout:
			break collectLoop
		}
	}

	// Should only receive non-empty logs
	expected := []string{"Log 1", "Log 2", "Log 3"}
	if len(receivedLogs) != len(expected) {
		t.Errorf("Expected %d logs (empty lines ignored), got %d", len(expected), len(receivedLogs))
	}

	for i, exp := range expected {
		if i >= len(receivedLogs) {
			continue
		}
		if receivedLogs[i] != exp {
			t.Errorf("Log at index %d: expected '%s', got '%s'", i, exp, receivedLogs[i])
		}
	}
}

func TestFileCleared(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}

	// Write initial logs
	f.WriteString("Initial log 1\n")
	f.WriteString("Initial log 2\n")
	f.Close()

	watcher := New(logFile)

	// Start watcher
	go watcher.Start()
	defer watcher.Stop()

	// Give watcher time to initialize
	time.Sleep(200 * time.Millisecond)

	// Clear file (truncate)
	err = os.Truncate(logFile, 0)
	if err != nil {
		t.Fatalf("Failed to truncate file: %v", err)
	}

	// Write new logs after clearing
	f, err = os.OpenFile(logFile, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		t.Fatalf("Failed to open log file: %v", err)
	}

	newLogs := []string{"After clear 1", "After clear 2"}
	for _, log := range newLogs {
		f.WriteString(log + "\n")
	}
	f.Close()

	// Collect new logs
	receivedLogs := make([]string, 0)
	timeout := time.After(2 * time.Second)

collectLoop:
	for i := 0; i < len(newLogs); i++ {
		select {
		case log := <-watcher.LogChan():
			receivedLogs = append(receivedLogs, log)
		case <-timeout:
			break collectLoop
		}
	}

	// Should receive logs after clear
	if len(receivedLogs) != len(newLogs) {
		t.Errorf("Expected %d logs after clear, got %d", len(newLogs), len(receivedLogs))
	}
}

func TestChannelBuffering(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}
	f.Close()

	watcher := New(logFile)

	// Start watcher
	go watcher.Start()
	defer watcher.Stop()

	// Give watcher time to initialize
	time.Sleep(200 * time.Millisecond)

	// Write many logs quickly (more than channel buffer size of 100)
	f, err = os.OpenFile(logFile, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		t.Fatalf("Failed to open log file: %v", err)
	}

	numLogs := 150
	for i := 0; i < numLogs; i++ {
		f.WriteString(fmt.Sprintf("Log %d\n", i))
	}
	f.Close()

	// Give time for file events
	time.Sleep(500 * time.Millisecond)

	// Collect logs - should get at least buffer size worth
	receivedCount := 0
	timeout := time.After(2 * time.Second)

collectLoop:
	for {
		select {
		case <-watcher.LogChan():
			receivedCount++
		case <-timeout:
			break collectLoop
		default:
			// Channel empty
			time.Sleep(100 * time.Millisecond)
			break collectLoop
		}
	}

	// Should receive logs (may not be all if channel is full)
	if receivedCount == 0 {
		t.Error("Expected to receive some logs, got 0")
	}

	// Channel has buffer of 100, so we should get at least some logs
	if receivedCount > numLogs {
		t.Errorf("Received more logs (%d) than written (%d)", receivedCount, numLogs)
	}
}

func TestSimulateLogWrite(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	// Test the helper function
	testLogs := []string{"Test log 1", "Test log 2", "Test log 3"}
	SimulateLogWrite(logFile, testLogs)

	// Verify logs were written
	content, err := os.ReadFile(logFile)
	if err != nil {
		t.Fatalf("Failed to read log file: %v", err)
	}

	contentStr := string(content)
	for _, log := range testLogs {
		if !contains(contentStr, log) {
			t.Errorf("Expected log file to contain '%s'", log)
		}
	}
}

func TestMultipleWrites(t *testing.T) {
	// Create temporary log file
	tmpDir := t.TempDir()
	logFile := filepath.Join(tmpDir, "test.log")

	f, err := os.Create(logFile)
	if err != nil {
		t.Fatalf("Failed to create test log file: %v", err)
	}
	f.Close()

	watcher := New(logFile)

	// Start watcher
	go watcher.Start()
	defer watcher.Stop()

	// Give watcher time to initialize
	time.Sleep(200 * time.Millisecond)

	receivedLogs := make([]string, 0)
	done := make(chan bool)

	// Collect logs in background
	go func() {
		timeout := time.After(3 * time.Second)
		for {
			select {
			case log := <-watcher.LogChan():
				receivedLogs = append(receivedLogs, log)
			case <-timeout:
				done <- true
				return
			}
		}
	}()

	// Write logs in multiple batches
	batches := [][]string{
		{"Batch 1 Log 1", "Batch 1 Log 2"},
		{"Batch 2 Log 1", "Batch 2 Log 2"},
		{"Batch 3 Log 1", "Batch 3 Log 2"},
	}

	for _, batch := range batches {
		f, err := os.OpenFile(logFile, os.O_APPEND|os.O_WRONLY, 0644)
		if err != nil {
			t.Fatalf("Failed to open log file: %v", err)
		}
		for _, log := range batch {
			f.WriteString(log + "\n")
		}
		f.Close()
		time.Sleep(300 * time.Millisecond) // Time between batches
	}

	<-done

	// Should receive all logs
	expectedTotal := 0
	for _, batch := range batches {
		expectedTotal += len(batch)
	}

	if len(receivedLogs) != expectedTotal {
		t.Errorf("Expected %d total logs, got %d", expectedTotal, len(receivedLogs))
	}
}

// Helper function
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr || containsMiddle(s, substr)))
}

func containsMiddle(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
