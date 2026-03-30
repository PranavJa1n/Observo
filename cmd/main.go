package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/PranavJa1n/Observo/internal/buffer"
	"github.com/PranavJa1n/Observo/internal/config"
	"github.com/PranavJa1n/Observo/internal/daemon"
	"github.com/PranavJa1n/Observo/internal/models"
	client "github.com/PranavJa1n/Observo/internal/python_client"
	"github.com/PranavJa1n/Observo/internal/server"
	"github.com/PranavJa1n/Observo/internal/watcher"
	"github.com/spf13/cobra"
)

func main() {

	rootCmd := &cobra.Command{ // creating the root command
		Use:   "observo",
		Short: "Intelligent log analysis with AI",
		Long:  `Observo monitors your application logs, uses clustering to identify bad logs, and provides AI-powered root cause analysis.`,
		CompletionOptions: cobra.CompletionOptions{
			DisableDefaultCmd: true, // Disable the auto-generated completion command
		},
	}

	rootCmd.AddCommand(initCmd) // adding the sub commands
	rootCmd.AddCommand(startCmd)
	rootCmd.AddCommand(stopCmd)
	rootCmd.AddCommand(statusCmd)
	rootCmd.AddCommand(configCmd)

	if err := rootCmd.Execute(); err != nil { // executing the commands
		fmt.Println(err)
		os.Exit(1)
	}
}

// INIT COMMAND - Interactive setup
var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize Observo configuration",
	Long:  "Interactive setup to create ~/.observo/config.json",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Observo Configuration Setup")
		fmt.Print("================================\n\n")

		if _, err := os.Stat(config.GetConfigPath()); err == nil { // if config already created
			fmt.Print("Config already exists. Overwrite? (y/n): ")
			reader := bufio.NewReader(os.Stdin)
			answer, _ := reader.ReadString('\n')
			if !strings.HasPrefix(strings.ToLower(strings.TrimSpace(answer)), "y") {
				fmt.Println("Cancelled.")
				return
			}
		}

		reader := bufio.NewReader(os.Stdin)

		fmt.Print("Enter log file or directory path: ") // asking for the log file path
		logPath, _ := reader.ReadString('\n')
		logPath = strings.TrimSpace(logPath)

		if _, err := os.Stat(logPath); os.IsNotExist(err) { // checking if the path exists
			fmt.Printf("Path does not exist: %s\n", logPath)
			return
		}

		fmt.Print("Enter alert email (optional, press Enter to skip): ") // asking for the alert email
		email, _ := reader.ReadString('\n')
		email = strings.TrimSpace(email)

		fmt.Print("Enter Google API key: ") // asking for the API key
		apiKey, _ := reader.ReadString('\n')
		apiKey = strings.TrimSpace(apiKey)

		cfg := &config.Config{ // creating the config
			Source:     "local",
			Path:       logPath,
			AlertEmail: email,
			APIKey:     apiKey,
		}

		if err := cfg.Validate(); err != nil { // validating the given data
			fmt.Printf("Validation failed: %v\n", err)
			return
		}

		if err := cfg.Save(); err != nil { // saving the config
			fmt.Printf("Failed to save config: %v\n", err)
			return
		}

		fmt.Println("\nConfiguration saved successfully!")
		fmt.Printf("Config file: %s\n", config.GetConfigPath())
		fmt.Println("\nNext step: Run 'observo start' to begin monitoring")
	},
}

// START COMMAND - Start monitoring
var startCmd = &cobra.Command{
	Use:   "start",
	Short: "Start Observo monitoring",
	Long:  "Starts file watching, log processing, and web dashboard. Use --daemon to run in background.",
	Run: func(cmd *cobra.Command, args []string) {
		// Check if --daemon flag is set
		daemonMode, _ := cmd.Flags().GetBool("daemon")
		foreground, _ := cmd.Flags().GetBool("foreground")

		// If daemon mode, start daemon and exit
		if daemonMode {
			if err := daemon.StartDaemon(); err != nil {
				fmt.Printf("❌ Failed to start daemon: %v\n", err)
				os.Exit(1)
			}
			return
		}

		// Load config
		cfg, err := config.Load()
		if err != nil {
			fmt.Println("❌ Error:", err)
			fmt.Println("💡 Run 'observo init' first to create configuration")
			return
		}

		// Validate config
		if err := cfg.Validate(); err != nil {
			fmt.Println("❌ Invalid config:", err)
			fmt.Println("💡 Run 'observo init' to fix configuration")
			return
		}

		// Print startup message (only if not foreground/daemon spawned process)
		if !foreground {
			fmt.Println("🚀 Starting Observo...")
			fmt.Println("================================")
			fmt.Printf("📁 Watching: %s\n", cfg.Path)
			fmt.Println("🌐 Dashboard: http://localhost:6969")
			fmt.Println("🐍 Python Service: http://localhost:5000")
			fmt.Print("\nPress Ctrl+C to stop\n\n")
		}

		// Run the main loop
		if err := run(cfg); err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			os.Exit(1)
		}
	},
}

// run is the main application loop
// This is where all the magic happens!
func run(cfg *config.Config) error {
	// 1. Start Python service
	fmt.Println("🐍 Starting Python service...")
	// ensure that python command will work on windows as well as linux
	pythonBin := "python"
	if _, err := exec.LookPath("python3"); err == nil {
		pythonBin = "python3"
	}
	pythonCmd := exec.Command(pythonBin, "python/main.py")

	pythonCmd.Env = append(os.Environ(), "ANTHROPIC_API_KEY="+cfg.APIKey)
	pythonCmd.Stdout = os.Stdout
	pythonCmd.Stderr = os.Stderr

	if err := pythonCmd.Start(); err != nil {
		return fmt.Errorf("failed to start Python service: %v", err)
	}
	defer pythonCmd.Process.Kill() // Stop Python when Go exits

	// Wait for Python to be ready
	pythonClient := client.New("http://localhost:5000")
	if err := pythonClient.WaitForPython(30 * time.Second); err != nil {
		return err
	}

	// 2. Initialize database
	fmt.Println("💾 Initializing database...")
	db, err := models.InitDB(config.GetDBPath())
	if err != nil {
		return fmt.Errorf("failed to init database: %v", err)
	}

	// 3. Start file watcher
	fmt.Println("👀 Starting file watcher...")
	logWatcher := watcher.New(cfg.Path)
	go logWatcher.Start()
	defer logWatcher.Stop()

	// 4. Start buffer (batches logs every 60s or 1000 logs)
	fmt.Println("📦 Starting buffer...")
	logBuffer := buffer.New(1000, 60*time.Second)
	go logBuffer.Start()
	defer logBuffer.Stop()

	// 5. Connect watcher → buffer
	// (Read logs from watcher, add to buffer)
	go func() {
		for log := range logWatcher.LogChan() {
			logBuffer.Add(log)
		}
	}()

	// 6. Connect buffer → Python client
	// (Read batches from buffer, send to Python)
	go func() {
		for batch := range logBuffer.SendChan() {
			if err := pythonClient.SendBatch(batch); err != nil {
				fmt.Printf("⚠️  Failed to send batch: %v\n", err)
			}
		}
	}()

	// 7. Start HTTP server (serves dashboard and API)
	fmt.Println("🌐 Starting HTTP server...")
	httpServer := server.New(db)
	go httpServer.Start()

	fmt.Println("\n✅ Observo is running!")
	fmt.Print("================================\n\n")

	// 8. Wait for Ctrl+C to stop
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n\n👋 Stopping Observo...")
	fmt.Println("Cleaning up...")

	return nil
}

// =====================================================
// STOP COMMAND - Stop the daemon
// =====================================================
var stopCmd = &cobra.Command{
	Use:   "stop",
	Short: "Stop Observo daemon",
	Long:  "Stops the running Observo daemon process",
	Run: func(cmd *cobra.Command, args []string) {
		if err := daemon.StopDaemon(); err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			os.Exit(1)
		}
	},
}

// =====================================================
// STATUS COMMAND - Check if Observo is running
// =====================================================
var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Check Observo status",
	Long:  "Checks if Observo is currently running (daemon or foreground)",
	Run: func(cmd *cobra.Command, args []string) {
		// First check if daemon is running
		running, err := daemon.IsRunning()
		if err != nil {
			fmt.Printf("❌ Error checking daemon status: %v\n", err)
			return
		}

		if running {
			pid, _ := daemon.GetPID()
			fmt.Printf("✅ Observo daemon is running (PID %d)\n", pid)
			fmt.Println("🌐 Dashboard: http://localhost:6969")
			fmt.Println("📊 API: http://localhost:6969/api/incidents")
			fmt.Printf("📝 Logs: %s\n", config.GetLogPath())
			return
		}

		// If daemon not running, check if foreground process is running via API
		err = client.New("http://localhost:6969").HealthCheck()
		if err != nil {
			fmt.Println("❌ Observo is not running")
			fmt.Println("💡 Run 'observo start' or 'observo start --daemon' to start monitoring")
			return
		}

		// If we got here, it's running in foreground
		fmt.Println("✅ Observo is running (foreground mode)")
		fmt.Println("🌐 Dashboard: http://localhost:6969")
		fmt.Println("📊 API: http://localhost:6969/api/incidents")
	},
}

// =====================================================
// CONFIG COMMAND - Update configuration
// =====================================================
var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Update Observo configuration",
	Long:  "Update specific configuration values",
	Run: func(cmd *cobra.Command, args []string) {
		// Load existing config
		cfg, err := config.Load()
		if err != nil {
			fmt.Println("❌ Error:", err)
			fmt.Println("💡 Run 'observo init' first")
			return
		}

		// Get flags
		source, _ := cmd.Flags().GetString("source")
		path, _ := cmd.Flags().GetString("path")
		email, _ := cmd.Flags().GetString("alert-email")
		apiKey, _ := cmd.Flags().GetString("api-key")

		// Update fields if flags were provided
		changed := false
		if source != "" {
			cfg.Source = source
			changed = true
		}
		if path != "" {
			cfg.Path = path
			changed = true
		}
		if email != "" {
			cfg.AlertEmail = email
			changed = true
		}
		if apiKey != "" {
			cfg.APIKey = apiKey
			changed = true
		}

		if !changed {
			fmt.Println("No changes specified. Use flags:")
			fmt.Println("  --source local")
			fmt.Println("  --path /path/to/logs")
			fmt.Println("  --alert-email user@email.com")
			fmt.Println("  --api-key sk-ant-...")
			return
		}

		// Validate
		if err := cfg.Validate(); err != nil {
			fmt.Printf("❌ Validation failed: %v\n", err)
			return
		}

		// Save
		if err := cfg.Save(); err != nil {
			fmt.Printf("❌ Failed to save: %v\n", err)
			return
		}

		fmt.Println("✅ Configuration updated successfully!")
	},
}

func init() {
	// Add flags to start command
	startCmd.Flags().BoolP("daemon", "d", false, "Run in daemon mode (background)")
	startCmd.Flags().Bool("foreground", false, "Internal flag for daemon spawned process")
	startCmd.Flags().MarkHidden("foreground") // Hide from help text

	// Add flags to config command
	configCmd.Flags().String("source", "", "Set source type (local)")
	configCmd.Flags().String("path", "", "Set log file/directory path")
	configCmd.Flags().String("alert-email", "", "Set alert email address")
	configCmd.Flags().String("api-key", "", "Set Anthropic API key")
}
