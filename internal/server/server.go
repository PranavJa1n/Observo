package server

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/PranavJa1n/Observo/internal/models"
	"github.com/gorilla/mux"
	"github.com/rs/cors"
	"gorm.io/gorm"
)

type Server struct {
	router    *mux.Router // HTTP router
	db        *gorm.DB    // DB connection
	startTime time.Time   // track when the server started
}

func New(db *gorm.DB) *Server { // function creates new HTTP server
	s := &Server{
		router:    mux.NewRouter(),
		db:        db,
		startTime: time.Now(),
	}
	s.setupRoutes()
	return s
}

func (s *Server) setupRoutes() { // function configure HTTP endpoints

	s.router.HandleFunc("/api/incidents", s.getIncidents).Methods("GET")
	s.router.HandleFunc("/api/stats", s.getStats).Methods("GET")

	// Serve the React dashboard build files
	distPath := s.getDashboardPath()
	if distPath != "" {
		// Serve static assets (JS, CSS, images) from the dist folder
		fs := http.FileServer(http.Dir(distPath))
		// Catch-all: serve index.html for any non-API route (React SPA routing)
		s.router.PathPrefix("/").Handler(spaHandler{staticHandler: fs, distPath: distPath})
	} else {
		// Fallback: serve the built-in HTML dashboard if no React build is found
		s.router.HandleFunc("/", s.serveFallbackDashboard).Methods("GET")
	}
}

// getDashboardPath finds the React dashboard build directory
func (s *Server) getDashboardPath() string {
	// Check relative to OBSERVO_HOME first
	observoHome := os.Getenv("OBSERVO_HOME")
	if observoHome != "" {
		distPath := filepath.Join(observoHome, "frontend", "main", "dist")
		if _, err := os.Stat(distPath); err == nil {
			fmt.Printf("📊 Serving React dashboard from: %s\n", distPath)
			return distPath
		}
	}

	// Check relative to current working directory
	distPath := filepath.Join("frontend", "main", "dist")
	if _, err := os.Stat(distPath); err == nil {
		fmt.Printf("📊 Serving React dashboard from: %s\n", distPath)
		return distPath
	}

	fmt.Println("⚠️  React dashboard build not found. Run: cd frontend/main && npm run build")
	fmt.Println("   Serving fallback dashboard instead.")
	return ""
}

// spaHandler serves static files, falling back to index.html for SPA routes
type spaHandler struct {
	staticHandler http.Handler
	distPath      string
}

func (h spaHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Check if the requested file exists in the dist folder
	path := filepath.Join(h.distPath, r.URL.Path)
	_, err := os.Stat(path)
	if os.IsNotExist(err) {
		// File doesn't exist — serve index.html (let React Router handle it)
		http.ServeFile(w, r, filepath.Join(h.distPath, "index.html"))
		return
	}
	// File exists — serve it directly (JS, CSS, images, etc.)
	h.staticHandler.ServeHTTP(w, r)
}

func (s *Server) Start() error { // function starts the HTTP server
	corsHandler := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE"},
		AllowedHeaders: []string{"Content-Type"},
	})

	handler := corsHandler.Handler(s.router)

	fmt.Println("Dashboard available at: http://localhost:6969")

	return http.ListenAndServe(":6969", handler)
}

func (s *Server) getIncidents(w http.ResponseWriter, r *http.Request) { // function gives us all the incidents from the db
	var incidents []models.Incident

	result := s.db.Order("created_at DESC").Find(&incidents) // getting all the indicents from db in descending order
	if result.Error != nil {
		http.Error(w, result.Error.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json") // return them as json
	json.NewEncoder(w).Encode(incidents)
}

func (s *Server) getStats(w http.ResponseWriter, r *http.Request) { // function returns the stats of the server like count of incidents and uptime
	var count int64

	s.db.Model(&models.Incident{}).Count(&count) // count the number of the incident

	uptime := time.Since(s.startTime) // getting the uptime
	
	hours := int(uptime.Hours())
	minutes := int(uptime.Minutes()) % 60
	seconds := int(uptime.Seconds()) % 60

	var uptimeHuman string
	if hours > 0 {
		uptimeHuman = fmt.Sprintf("%dh %dmin %ds", hours, minutes, seconds)
	} else if minutes > 0 {
		uptimeHuman = fmt.Sprintf("%dmin %ds", minutes, seconds)
	} else {
		uptimeHuman = fmt.Sprintf("%ds", seconds)
	}

	stats := map[string]interface{}{
		"running":         true,
		"incidents_count": count,
		"uptime_seconds":  int(uptime.Seconds()),
		"uptime_human":    uptimeHuman,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func (s *Server) serveFallbackDashboard(w http.ResponseWriter, r *http.Request) { // Fallback HTML page when React build is missing
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Observo Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 80px auto;
            padding: 20px;
            background: #0a0a0a;
            color: #e2e8f0;
        }
        .card {
            background: #111;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #222;
            margin-bottom: 20px;
        }
        h1 { color: #f59e0b; }
        .stat { font-size: 2em; font-weight: bold; color: #22c55e; }
        .hint { color: #666; margin-top: 30px; font-size: 0.9em; }
        code { background: #1a1a1a; padding: 4px 8px; border-radius: 4px; color: #f59e0b; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Observo Dashboard</h1>
        <p>AI-Powered Log Analysis</p>
    </div>
    <div class="card">
        <div class="stat" id="incidentCount">...</div>
        <div>Total Incidents</div>
    </div>
    <div class="card">
        <div class="stat" id="uptime">...</div>
        <div>Uptime</div>
    </div>
    <div class="card" id="incidentsList">Loading...</div>
    <p class="hint">
        For the full React dashboard, run:<br>
        <code>cd frontend/main && npm install && npm run build</code><br>
        then restart Observo.
    </p>
    <script>
        fetch('/api/stats')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                document.getElementById('incidentCount').textContent = data.incidents_count;
                document.getElementById('uptime').textContent = data.uptime_human;
            });
        fetch('/api/incidents')
            .then(function(r) { return r.json(); })
            .then(function(incidents) {
                var list = document.getElementById('incidentsList');
                if (!incidents || incidents.length === 0) {
                    list.innerHTML = '<p>No incidents detected yet. Observo is monitoring your logs...</p>';
                    return;
                }
                var html = '';
                for (var i = 0; i < incidents.length; i++) {
                    var inc = incidents[i];
                    html += '<div style="border-left:3px solid #f59e0b; padding:12px; margin:8px 0; background:#1a1a1a; border-radius:6px;">';
                    html += '<h3>' + (inc.problem || 'Anomaly Detected') + '</h3>';
                    html += '<p>' + (inc.ai_summary || 'Processing...') + '</p>';
                    html += '<p style="color:#666">' + new Date(inc.created_at).toLocaleString() + '</p>';
                    html += '</div>';
                }
                list.innerHTML = html;
            });
        setInterval(function() { location.reload(); }, 10000);
    </script>
</body>
</html>`

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}
