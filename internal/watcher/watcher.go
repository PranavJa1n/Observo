package watcher

import (
	"bufio"
	"fmt"
	"os"
	"time"

	"github.com/fsnotify/fsnotify"
)

type Watcher struct { // monitor the log file for the new line
	logPath  string      // path from where we have to take the logs
	logChan  chan string // channel to send the logs
	stopChan chan bool   // channel signal to stop
	lastSize int64       // tracking the file size of the log file so that only new logs are send to the channel
}

func New(logPath string) *Watcher { // function to create a watcher
	return &Watcher{
		logPath:  logPath,
		logChan:  make(chan string, 100), // channel size of 100
		stopChan: make(chan bool),
		lastSize: 0, // 0 because for the starting the size of log file will be 0
	}
}

func (w *Watcher) Start() error { // function will start watching the log file
	// fsnotify is a Go library to provide cross-platform filesystem notifications
	watcher, err := fsnotify.NewWatcher() // creating a new watch file
	if err != nil {
		return fmt.Errorf("failed to create watcher: %v", err)
	}
	defer watcher.Close()

	err = watcher.Add(w.logPath) // adding the log file to the watch file
	if err != nil {
		return fmt.Errorf("failed to watch file: %v", err)
	}

	fileInfo, err := os.Stat(w.logPath) // getting the inital log file size
	if err == nil {
		w.lastSize = fileInfo.Size()
	}

	fmt.Printf("Watching log file: %s\n", w.logPath)

	// Watch for file changes in a loop
	for {
		select {
		case event := <-watcher.Events: // log file modified
			if event.Op&fsnotify.Write == fsnotify.Write {
				w.readNewLines()
			}

		case err := <-watcher.Errors:
			fmt.Printf("Watcher error: %v\n", err)

		case <-w.stopChan: // stop signal recieved
			fmt.Println("Stopping watcher file")
			return nil
		}
	}
}

func (w *Watcher) readNewLines() { // function reads only the new line from the log file and then add them in the watcher
	file, err := os.Open(w.logPath)
	if err != nil {
		return
	}
	defer file.Close()

	fileInfo, err := file.Stat() // get current file size
	if err != nil {
		return
	}
	currentSize := fileInfo.Size()

	if currentSize < w.lastSize { // if file was cleared then reset our size
		w.lastSize = 0
	}

	file.Seek(w.lastSize, 0) // seeking to the last read part of the log file

	scanner := bufio.NewScanner(file) // reads new logs from the log file
	for scanner.Scan() {
		line := scanner.Text()
		if line != "" {
			select { // send logs to the channel if channel is not full
			case w.logChan <- line:
			default: // if channel is full then no line send
			}
		}
	}

	w.lastSize = currentSize // updating the lsat read position
}

func (w *Watcher) LogChan() <-chan string { // function gives us the channel that recieves the logs
	return w.logChan
}

func (w *Watcher) Stop() { // function gives us the signal to stop the channel if the channel is full
	w.stopChan <- true
	close(w.logChan)
}

func SimulateLogWrite(logPath string, lines []string) { // helper function for testing that writes test logs to the file being watched
	file, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer file.Close()

	for _, line := range lines {
		file.WriteString(line + "\n")
		time.Sleep(10 * time.Millisecond)
	}
}
