package server

import (
	"encoding/json"
	"fmt"
	"net/http"
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
	s.router.HandleFunc("/", s.serveDashboard).Methods("GET") // going to serve the REACT frontend (for now it is just serving basic html)
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

	stats := map[string]interface{}{
		"running":         true,
		"incidents_count": count,
		"uptime_seconds":  int(uptime.Seconds()),
		"uptime_human":    uptime.String(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func (s *Server) serveDashboard(w http.ResponseWriter, r *http.Request) { // Simple HTML page that is going to be served from now
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Observo Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .incidents {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .incident {
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            background: #f9f9f9;
        }
        .incident-time {
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Observo Dashboard</h1>
        <p>AI-Powered Log Analysis</p>
    </div>

    <div class="stats" id="stats">
        <div class="stat-card">
            <div class="stat-value" id="incidentCount">...</div>
            <div>Total Incidents</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="uptime">...</div>
            <div>Uptime</div>
        </div>
    </div>

    <div class="incidents">
        <h2>Recent Incidents</h2>
        <div id="incidentsList">Loading...</div>
    </div>

    <script>
        // Fetch stats
        fetch('/api/stats')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                document.getElementById('incidentCount').textContent = data.incidents_count;
                document.getElementById('uptime').textContent = data.uptime_human;
            });

        // Fetch incidents
        fetch('/api/incidents')
            .then(function(r) { return r.json(); })
            .then(function(incidents) {
                var list = document.getElementById('incidentsList');
                if (incidents.length === 0) {
                    list.innerHTML = '<p>No incidents detected yet. Observo is monitoring your logs...</p>';
                    return;
                }
                
                var html = '';
                for (var i = 0; i < incidents.length; i++) {
                    var inc = incidents[i];
                    html += '<div class="incident">';
                    html += '<h3>' + (inc.problem || 'Anomaly Detected') + '</h3>';
                    html += '<p><strong>Summary:</strong> ' + (inc.ai_summary || 'Processing...') + '</p>';
                    html += '<p><strong>Root Cause:</strong> ' + (inc.root_cause || 'Analyzing...') + '</p>';
                    html += '<p class="incident-time">' + new Date(inc.created_at).toLocaleString() + '</p>';
                    html += '</div>';
                }
                list.innerHTML = html;
            });

        // Auto-refresh every 10 seconds
        setInterval(function() { location.reload(); }, 10000);
    </script>
</body>
</html>`

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}
