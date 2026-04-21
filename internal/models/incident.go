package models

import (
	"time"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

// Incident represents a detected log anomaly
type Incident struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	ClusterID   string    `gorm:"index" json:"cluster_id"`
	Timestamp   time.Time `json:"timestamp"`
	Problem     string    `json:"problem"`
	AISummary   string    `json:"ai_summary"`
	RootCause   string    `json:"root_cause"`
	Suggestions string    `json:"suggestions"`
	SampleLogs  string    `json:"sample_logs"`
	Severity    string    `json:"severity"`
	CreatedAt   time.Time `json:"created_at"`
}

func InitDB(dbPath string) (*gorm.DB, error) { // open DB or create table if needed
	db, err := gorm.Open(sqlite.Open(dbPath), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	err = db.AutoMigrate(&Incident{}) // AutoMograte - Create table if not exist
	if err != nil {
		return nil, err
	}

	return db, nil
}
