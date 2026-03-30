package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestGetObservoDir(t *testing.T) {
	dir := GetObservoDir()

	if dir == "" {
		t.Error("GetObservoDir() returned empty string")
	}

	// Should contain .observo
	if !contains(dir, ".observo") {
		t.Errorf("Expected directory to contain '.observo', got: %s", dir)
	}

	// Should be absolute path
	if !filepath.IsAbs(dir) {
		t.Errorf("Expected absolute path, got: %s", dir)
	}
}

func TestGetConfigPath(t *testing.T) {
	path := GetConfigPath()

	if path == "" {
		t.Error("GetConfigPath() returned empty string")
	}

	// Should end with config.json
	if filepath.Base(path) != "config.json" {
		t.Errorf("Expected path to end with 'config.json', got: %s", path)
	}

	// Should be absolute path
	if !filepath.IsAbs(path) {
		t.Errorf("Expected absolute path, got: %s", path)
	}

	// Should contain .observo
	if !contains(path, ".observo") {
		t.Errorf("Expected path to contain '.observo', got: %s", path)
	}
}

func TestGetDBPath(t *testing.T) {
	path := GetDBPath()

	if path == "" {
		t.Error("GetDBPath() returned empty string")
	}

	// Should end with observo.db
	if filepath.Base(path) != "observo.db" {
		t.Errorf("Expected path to end with 'observo.db', got: %s", path)
	}

	// Should be absolute path
	if !filepath.IsAbs(path) {
		t.Errorf("Expected absolute path, got: %s", path)
	}

	// Should contain .observo
	if !contains(path, ".observo") {
		t.Errorf("Expected path to contain '.observo', got: %s", path)
	}
}

func TestGetPIDPath(t *testing.T) {
	path := GetPIDPath()

	if path == "" {
		t.Error("GetPIDPath() returned empty string")
	}

	// Should end with observo.pid
	if filepath.Base(path) != "observo.pid" {
		t.Errorf("Expected path to end with 'observo.pid', got: %s", path)
	}

	// Should be absolute path
	if !filepath.IsAbs(path) {
		t.Errorf("Expected absolute path, got: %s", path)
	}

	// Should contain .observo
	if !contains(path, ".observo") {
		t.Errorf("Expected path to contain '.observo', got: %s", path)
	}
}

func TestGetLogPath(t *testing.T) {
	path := GetLogPath()

	if path == "" {
		t.Error("GetLogPath() returned empty string")
	}

	// Should end with observo.log
	if filepath.Base(path) != "observo.log" {
		t.Errorf("Expected path to end with 'observo.log', got: %s", path)
	}

	// Should be absolute path
	if !filepath.IsAbs(path) {
		t.Errorf("Expected absolute path, got: %s", path)
	}

	// Should contain .observo
	if !contains(path, ".observo") {
		t.Errorf("Expected path to contain '.observo', got: %s", path)
	}
}

func TestPathsConsistency(t *testing.T) {
	// All paths should be in the same parent directory
	observoDir := GetObservoDir()

	paths := map[string]string{
		"config": GetConfigPath(),
		"db":     GetDBPath(),
		"pid":    GetPIDPath(),
		"log":    GetLogPath(),
	}

	for name, path := range paths {
		dir := filepath.Dir(path)
		if dir != observoDir {
			t.Errorf("Path '%s' is not in observo directory. Expected dir: %s, got: %s", name, observoDir, dir)
		}
	}
}

func TestPathsAreUnique(t *testing.T) {
	paths := []string{
		GetConfigPath(),
		GetDBPath(),
		GetPIDPath(),
		GetLogPath(),
	}

	// Check that all paths are unique
	seen := make(map[string]bool)
	for _, path := range paths {
		if seen[path] {
			t.Errorf("Duplicate path found: %s", path)
		}
		seen[path] = true
	}
}

func TestObservoDirCreation(t *testing.T) {
	// Get the observo directory
	observoDir := GetObservoDir()

	// This is a non-destructive test - we just verify the path makes sense
	// We won't actually create/delete directories in user's home

	// Verify it's based on home directory
	home, err := os.UserHomeDir()
	if err != nil {
		t.Skipf("Cannot get home directory: %v", err)
	}

	expectedDir := filepath.Join(home, ".observo")
	if observoDir != expectedDir {
		t.Errorf("Expected observo dir %s, got %s", expectedDir, observoDir)
	}
}

func TestPathsWithTempDir(t *testing.T) {
	// We can't easily override the home directory in tests,
	// so this test verifies the path structure is correct

	home, err := os.UserHomeDir()
	if err != nil {
		t.Skipf("Cannot get home directory: %v", err)
	}

	expectedObservoDir := filepath.Join(home, ".observo")
	expectedConfigPath := filepath.Join(expectedObservoDir, "config.json")
	expectedDBPath := filepath.Join(expectedObservoDir, "observo.db")
	expectedPIDPath := filepath.Join(expectedObservoDir, "observo.pid")
	expectedLogPath := filepath.Join(expectedObservoDir, "observo.log")

	if GetObservoDir() != expectedObservoDir {
		t.Errorf("GetObservoDir(): expected %s, got %s", expectedObservoDir, GetObservoDir())
	}

	if GetConfigPath() != expectedConfigPath {
		t.Errorf("GetConfigPath(): expected %s, got %s", expectedConfigPath, GetConfigPath())
	}

	if GetDBPath() != expectedDBPath {
		t.Errorf("GetDBPath(): expected %s, got %s", expectedDBPath, GetDBPath())
	}

	if GetPIDPath() != expectedPIDPath {
		t.Errorf("GetPIDPath(): expected %s, got %s", expectedPIDPath, GetPIDPath())
	}

	if GetLogPath() != expectedLogPath {
		t.Errorf("GetLogPath(): expected %s, got %s", expectedLogPath, GetLogPath())
	}
}

func TestPathFilenames(t *testing.T) {
	testCases := []struct {
		name     string
		pathFunc func() string
		expected string
	}{
		{"Config", GetConfigPath, "config.json"},
		{"DB", GetDBPath, "observo.db"},
		{"PID", GetPIDPath, "observo.pid"},
		{"Log", GetLogPath, "observo.log"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			path := tc.pathFunc()
			filename := filepath.Base(path)
			if filename != tc.expected {
				t.Errorf("Expected filename %s, got %s", tc.expected, filename)
			}
		})
	}
}

// Helper function to check if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && containsSubstring(s, substr))
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
