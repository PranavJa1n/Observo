package buffer

import (
	"fmt"
	"sync"
	"time"
)

// chan == channel in go it is a way of passing data between goroutines(lightweight fn in go)
// Buffer collect logs and sends them in batches
type Buffer struct {
	logs     []string
	maxSize  int           // send batch when this many logs (e.g., 1000)
	interval time.Duration // send batch after this time (e.g., 60 seconds)
	sendChan chan []string // Channel to send batch
	mu       sync.Mutex    // Prevent race condition
	stopChan chan bool     // Channel to signal stop
}

// New creates a new buffer
func New(maxSize int, interval time.Duration) *Buffer {
	return &Buffer{
		logs:     make([]string, 0, maxSize),
		maxSize:  maxSize,
		interval: interval,
		sendChan: make(chan []string, 10),
		stopChan: make(chan bool),
	}
}

func (b *Buffer) Add(log string) { // adds the logs to the buffer
	b.mu.Lock() // lock to prevent race confition
	defer b.mu.Unlock()

	b.logs = append(b.logs, log)

	if len(b.logs) >= b.maxSize {
		b.flushLocked() // Use locked version since we already have the lock
	}
}

func (b *Buffer) Start() { // it starts the timer based flushing of the logs
	ticker := time.NewTicker(b.interval)
	defer ticker.Stop()

	fmt.Printf("Buffer started: flush every %v or %d logs", b.interval, b.maxSize)
	fmt.Println()

	for {
		select {
		case <-ticker.C:
			b.Flush() // time expires flush buffer

		case <-b.stopChan:
			b.Flush() // if Stop Signal is recieved then flush buffer
			close(b.sendChan)
			return
		}
	}
}

func (b *Buffer) Flush() { // sends all the logs as a batch
	b.mu.Lock()
	defer b.mu.Unlock()
	b.flushLocked()
}

// flushLocked is the intern1al flush
func (b *Buffer) flushLocked() {
	if len(b.logs) == 0 { // only flush if there are logs
		return
	}

	batch := make([]string, len(b.logs)) // copy the batch so that we can clear the actual batch
	copy(batch, b.logs)

	select { // select is used ti wait on multiple channel operations
	case b.sendChan <- batch: // tries to send batch into sendChan channel
		fmt.Printf("Flushed batch: %d logs", len(batch))
		fmt.Println()
	default:
		fmt.Println("Send channel full, dropping batch")
		fmt.Println()
	}

	b.logs = b.logs[:0] // clear the buffer
}

func (b *Buffer) SendChan() <-chan []string { // returns the channel that recieves batch of logs
	return b.sendChan
}

func (b *Buffer) Stop() { // stop the buffer
	b.stopChan <- true
}

func (b *Buffer) GetStats() map[string]interface{} { // gives us the current buffer stats
	b.mu.Lock()
	defer b.mu.Unlock()

	return map[string]interface{}{
		"current_size": len(b.logs),
		"max_size":     b.maxSize,
		"interval":     b.interval.String(),
	}
}
