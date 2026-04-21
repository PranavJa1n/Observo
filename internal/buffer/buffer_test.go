package buffer

import (
	"sync"
	"testing"
	"time"
)

func TestNew(t *testing.T) {
	maxSize := 100
	interval := 10 * time.Second

	buffer := New(maxSize, interval)

	if buffer == nil {
		t.Fatal("New() returned nil")
	}

	if buffer.maxSize != maxSize {
		t.Errorf("Expected maxSize %d, got %d", maxSize, buffer.maxSize)
	}

	if buffer.interval != interval {
		t.Errorf("Expected interval %v, got %v", interval, buffer.interval)
	}

	if len(buffer.logs) != 0 {
		t.Errorf("Expected empty logs slice, got %d items", len(buffer.logs))
	}

	if buffer.sendChan == nil {
		t.Error("sendChan should not be nil")
	}

	if buffer.stopChan == nil {
		t.Error("stopChan should not be nil")
	}
}

func TestAdd(t *testing.T) {
	buffer := New(100, 10*time.Second)

	testLog := "Test log line"
	buffer.Add(testLog)

	buffer.mu.Lock()
	defer buffer.mu.Unlock()

	if len(buffer.logs) != 1 {
		t.Errorf("Expected 1 log, got %d", len(buffer.logs))
	}

	if buffer.logs[0] != testLog {
		t.Errorf("Expected log '%s', got '%s'", testLog, buffer.logs[0])
	}
}

func TestAddMultiple(t *testing.T) {
	buffer := New(100, 10*time.Second)

	testLogs := []string{"Log 1", "Log 2", "Log 3"}
	for _, log := range testLogs {
		buffer.Add(log)
	}

	buffer.mu.Lock()
	defer buffer.mu.Unlock()

	if len(buffer.logs) != len(testLogs) {
		t.Errorf("Expected %d logs, got %d", len(testLogs), len(buffer.logs))
	}

	for i, log := range testLogs {
		if buffer.logs[i] != log {
			t.Errorf("Expected log at index %d to be '%s', got '%s'", i, log, buffer.logs[i])
		}
	}
}

func TestSizeBasedFlush(t *testing.T) {
	maxSize := 5
	buffer := New(maxSize, 1*time.Minute)

	// Start buffer to handle sends
	go buffer.Start()
	defer buffer.Stop()

	// Add logs up to maxSize
	for i := 0; i < maxSize; i++ {
		buffer.Add("Log line")
	}

	// Wait for batch to be sent
	select {
	case batch := <-buffer.SendChan():
		if len(batch) != maxSize {
			t.Errorf("Expected batch size %d, got %d", maxSize, len(batch))
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Timeout waiting for batch")
	}

	// Buffer should be empty after flush
	buffer.mu.Lock()
	defer buffer.mu.Unlock()
	if len(buffer.logs) != 0 {
		t.Errorf("Expected empty buffer after flush, got %d logs", len(buffer.logs))
	}
}

func TestTimeBasedFlush(t *testing.T) {
	interval := 500 * time.Millisecond
	buffer := New(1000, interval)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// Add a few logs (less than maxSize)
	testLogs := []string{"Log 1", "Log 2", "Log 3"}
	for _, log := range testLogs {
		buffer.Add(log)
	}

	// Wait for time-based flush
	select {
	case batch := <-buffer.SendChan():
		if len(batch) != len(testLogs) {
			t.Errorf("Expected batch size %d, got %d", len(testLogs), len(batch))
		}
		for i, log := range testLogs {
			if batch[i] != log {
				t.Errorf("Expected batch[%d] to be '%s', got '%s'", i, log, batch[i])
			}
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Timeout waiting for time-based flush")
	}
}

func TestFlushEmptyBuffer(t *testing.T) {
	buffer := New(100, 1*time.Second)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// Flush empty buffer
	buffer.Flush()

	// Should not send anything
	select {
	case <-buffer.SendChan():
		t.Error("Should not send batch for empty buffer")
	case <-time.After(100 * time.Millisecond):
		// Expected - no batch sent
	}
}

func TestStop(t *testing.T) {
	buffer := New(100, 1*time.Second)

	// Start buffer
	done := make(chan bool)
	go func() {
		buffer.Start()
		done <- true
	}()

	// Add some logs
	buffer.Add("Log 1")
	buffer.Add("Log 2")

	// Stop buffer
	buffer.Stop()

	// Should flush remaining logs
	select {
	case batch := <-buffer.SendChan():
		if len(batch) != 2 {
			t.Errorf("Expected final batch size 2, got %d", len(batch))
		}
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for final flush on stop")
	}

	// Wait for Start() to return
	select {
	case <-done:
		// Expected
	case <-time.After(1 * time.Second):
		t.Fatal("Start() did not return after Stop()")
	}

	// sendChan should be closed
	_, ok := <-buffer.SendChan()
	if ok {
		t.Error("sendChan should be closed after Stop()")
	}
}

func TestGetStats(t *testing.T) {
	maxSize := 100
	interval := 10 * time.Second
	buffer := New(maxSize, interval)

	// Add some logs
	buffer.Add("Log 1")
	buffer.Add("Log 2")
	buffer.Add("Log 3")

	stats := buffer.GetStats()

	if stats["current_size"] != 3 {
		t.Errorf("Expected current_size 3, got %v", stats["current_size"])
	}

	if stats["max_size"] != maxSize {
		t.Errorf("Expected max_size %d, got %v", maxSize, stats["max_size"])
	}

	if stats["interval"] != interval.String() {
		t.Errorf("Expected interval %s, got %v", interval.String(), stats["interval"])
	}
}

func TestConcurrentAdd(t *testing.T) {
	buffer := New(1000, 10*time.Second)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// Concurrent adds
	numGoroutines := 10
	logsPerGoroutine := 10
	var wg sync.WaitGroup

	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < logsPerGoroutine; j++ {
				buffer.Add("Log from goroutine")
			}
		}(i)
	}

	wg.Wait()

	// Check total logs
	buffer.mu.Lock()
	totalLogs := len(buffer.logs)
	buffer.mu.Unlock()

	expectedTotal := numGoroutines * logsPerGoroutine
	if totalLogs != expectedTotal {
		t.Errorf("Expected %d logs after concurrent adds, got %d", expectedTotal, totalLogs)
	}
}

func TestMultipleFlushCycles(t *testing.T) {
	maxSize := 5
	buffer := New(maxSize, 1*time.Minute)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// First batch
	for i := 0; i < maxSize; i++ {
		buffer.Add("Batch 1")
	}

	select {
	case batch := <-buffer.SendChan():
		if len(batch) != maxSize {
			t.Errorf("First batch: expected size %d, got %d", maxSize, len(batch))
		}
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for first batch")
	}

	// Second batch
	for i := 0; i < maxSize; i++ {
		buffer.Add("Batch 2")
	}

	select {
	case batch := <-buffer.SendChan():
		if len(batch) != maxSize {
			t.Errorf("Second batch: expected size %d, got %d", maxSize, len(batch))
		}
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for second batch")
	}
}

func TestSendChannelFull(t *testing.T) {
	// Create buffer with small send channel (capacity 10)
	buffer := New(5, 1*time.Minute)

	// Don't start buffer or consume from sendChan
	// This will cause the channel to fill up

	// Fill the send channel
	for i := 0; i < 10; i++ {
		buffer.Add("Log")
		buffer.Add("Log")
		buffer.Add("Log")
		buffer.Add("Log")
		buffer.Add("Log") // This will trigger flush
		// After a few iterations, sendChan should be full
	}

	// The buffer should handle full channel gracefully (drop batch)
	// No panic should occur
	buffer.mu.Lock()
	currentSize := len(buffer.logs)
	buffer.mu.Unlock()

	// Buffer should be empty or contain logs from the last incomplete batch
	if currentSize > 4 {
		t.Errorf("Expected buffer size <= 4 after flushes, got %d", currentSize)
	}
}

func TestFlushPreservesLogOrder(t *testing.T) {
	buffer := New(100, 1*time.Second)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// Add logs in specific order
	expectedOrder := []string{"Log A", "Log B", "Log C", "Log D", "Log E"}
	for _, log := range expectedOrder {
		buffer.Add(log)
	}

	// Manual flush
	buffer.Flush()

	// Check batch order
	select {
	case batch := <-buffer.SendChan():
		if len(batch) != len(expectedOrder) {
			t.Fatalf("Expected %d logs, got %d", len(expectedOrder), len(batch))
		}
		for i, expected := range expectedOrder {
			if batch[i] != expected {
				t.Errorf("Order mismatch at index %d: expected '%s', got '%s'", i, expected, batch[i])
			}
		}
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for batch")
	}
}

func TestBufferIsolation(t *testing.T) {
	buffer := New(10, 1*time.Second)

	// Start buffer
	go buffer.Start()
	defer buffer.Stop()

	// Add logs
	originalLogs := []string{"Log 1", "Log 2", "Log 3"}
	for _, log := range originalLogs {
		buffer.Add(log)
	}

	// Flush
	buffer.Flush()

	// Get batch
	select {
	case batch := <-buffer.SendChan():
		// Modify the batch
		batch[0] = "Modified"

		// Original buffer should not be affected
		buffer.Add("Log 4")
		buffer.mu.Lock()
		if buffer.logs[0] == "Modified" {
			t.Error("Buffer was not properly isolated from sent batch")
		}
		buffer.mu.Unlock()
	case <-time.After(1 * time.Second):
		t.Fatal("Timeout waiting for batch")
	}
}
