package config

import (
	"os"
	"testing"
	"time"
)

func TestLoad_Defaults(t *testing.T) {
	// Clear env vars that might be set
	clearEnv(t)
	defer clearEnv(t)

	cfg := Load()
	if cfg.BaseURL != DefaultBaseURL {
		t.Errorf("expected %s, got %s", DefaultBaseURL, cfg.BaseURL)
	}
	if cfg.APIKey != "" {
		t.Errorf("expected empty API key, got %s", cfg.APIKey)
	}
	if cfg.Timeout != time.Duration(DefaultTimeoutSeconds)*time.Second {
		t.Errorf("expected %ds timeout, got %s", DefaultTimeoutSeconds, cfg.Timeout)
	}
	if cfg.RetryMaxAttempts != DefaultRetryMaxAttempts {
		t.Errorf("expected %d, got %d", DefaultRetryMaxAttempts, cfg.RetryMaxAttempts)
	}
	if cfg.RetryBaseDelay != time.Duration(DefaultRetryBaseDelayMS)*time.Millisecond {
		t.Errorf("expected %dms, got %s", DefaultRetryBaseDelayMS, cfg.RetryBaseDelay)
	}
	if !cfg.RetryOn5xx {
		t.Error("expected RetryOn5xx to be true")
	}
	if cfg.InsecureSkipVerify {
		t.Error("expected InsecureSkipVerify to be false")
	}
}

func TestLoad_FromEnv(t *testing.T) {
	clearEnv(t)
	defer clearEnv(t)

	os.Setenv(EnvBaseURL, "https://qs.example.com:8443")
	os.Setenv(EnvAPIKey, "test-key-12345")
	os.Setenv(EnvTimeout, "15s")
	os.Setenv(EnvRetryMaxAttempts, "5")
	os.Setenv(EnvRetryBaseDelay, "2s")
	os.Setenv(EnvRetryOn5xx, "false")

	cfg := Load()
	if cfg.BaseURL != "https://qs.example.com:8443" {
		t.Errorf("expected https://qs.example.com:8443, got %s", cfg.BaseURL)
	}
	if cfg.APIKey != "test-key-12345" {
		t.Errorf("expected test-key-12345, got %s", cfg.APIKey)
	}
	if cfg.Timeout != 15*time.Second {
		t.Errorf("expected 15s, got %s", cfg.Timeout)
	}
	if cfg.RetryMaxAttempts != 5 {
		t.Errorf("expected 5, got %d", cfg.RetryMaxAttempts)
	}
	if cfg.RetryBaseDelay != 2*time.Second {
		t.Errorf("expected 2s, got %s", cfg.RetryBaseDelay)
	}
	if cfg.RetryOn5xx {
		t.Error("expected RetryOn5xx to be false")
	}
}

func TestLoad_FromEnvDurationAsInt(t *testing.T) {
	clearEnv(t)
	defer clearEnv(t)

	os.Setenv(EnvBaseURL, "http://localhost:8000")
	os.Setenv(EnvAPIKey, "test-key")
	os.Setenv(EnvTimeout, "10")   // seconds as int
	os.Setenv(EnvRetryBaseDelay, "1000") // ms as int

	cfg := Load()
	if cfg.Timeout != 10*time.Second {
		t.Errorf("expected 10s, got %s", cfg.Timeout)
	}
	if cfg.RetryBaseDelay != 1000*time.Millisecond {
		t.Errorf("expected 1000ms, got %s", cfg.RetryBaseDelay)
	}
}

func TestLoadFromMap(t *testing.T) {
	vars := map[string]string{
		EnvBaseURL:          "https://api.quantum-shield.io",
		EnvAPIKey:           "map-key",
		EnvTimeout:          "5s",
		EnvRetryMaxAttempts: "2",
		EnvRetryBaseDelay:   "250ms",
		EnvRetryOn5xx:       "true",
	}

	cfg := LoadFromMap(vars)
	if cfg.BaseURL != "https://api.quantum-shield.io" {
		t.Errorf("expected https://api.quantum-shield.io, got %s", cfg.BaseURL)
	}
	if cfg.APIKey != "map-key" {
		t.Errorf("expected map-key, got %s", cfg.APIKey)
	}
	if cfg.Timeout != 5*time.Second {
		t.Errorf("expected 5s, got %s", cfg.Timeout)
	}
	if cfg.RetryMaxAttempts != 2 {
		t.Errorf("expected 2, got %d", cfg.RetryMaxAttempts)
	}
	if cfg.RetryBaseDelay != 250*time.Millisecond {
		t.Errorf("expected 250ms, got %s", cfg.RetryBaseDelay)
	}
}

func TestClientOptions(t *testing.T) {
	cfg := &Config{
		BaseURL:            "http://test:8080",
		APIKey:             "key",
		Timeout:            10 * time.Second,
		RetryMaxAttempts:   2,
		RetryBaseDelay:     1 * time.Second,
		RetryOn5xx:         true,
		InsecureSkipVerify: false,
	}
	opts := cfg.ClientOptions()
	if opts.BaseURL != cfg.BaseURL {
		t.Errorf("expected %s, got %s", cfg.BaseURL, opts.BaseURL)
	}
	if opts.APIKey != cfg.APIKey {
		t.Errorf("expected %s, got %s", cfg.APIKey, opts.APIKey)
	}
}

func TestValidate(t *testing.T) {
	tests := []struct {
		name string
		cfg  *Config
		err  bool
	}{
		{"valid", &Config{BaseURL: "http://localhost:8000", Timeout: 30 * time.Second, RetryMaxAttempts: 3, RetryBaseDelay: 500 * time.Millisecond}, false},
		{"empty base URL", &Config{BaseURL: "", Timeout: 30 * time.Second, RetryMaxAttempts: 3, RetryBaseDelay: 500 * time.Millisecond}, true},
		{"zero timeout", &Config{BaseURL: "http://localhost:8000", Timeout: 0, RetryMaxAttempts: 3, RetryBaseDelay: 500 * time.Millisecond}, true},
		{"negative retry", &Config{BaseURL: "http://localhost:8000", Timeout: 30 * time.Second, RetryMaxAttempts: -1, RetryBaseDelay: 500 * time.Millisecond}, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.cfg.Validate()
			if (err != nil) != tt.err {
				t.Errorf("Validate() error = %v, wantErr = %v", err, tt.err)
			}
		})
	}
}

func TestString(t *testing.T) {
	cfg := &Config{
		BaseURL:          "http://localhost:8000",
		APIKey:           "my-secret-api-key-12345",
		Timeout:          30 * time.Second,
		RetryMaxAttempts: 3,
		RetryBaseDelay:   500 * time.Millisecond,
		RetryOn5xx:       true,
	}
	s := cfg.String()
	if s == "" {
		t.Error("expected non-empty string")
	}
	// API key should be masked
	if contains(s, "my-secret") {
		t.Error("API key should be masked in string output")
	}
}

func clearEnv(t *testing.T) {
	envVars := []string{
		EnvBaseURL, EnvAPIKey, EnvTimeout, EnvRetryMaxAttempts,
		EnvRetryBaseDelay, EnvRetryOn5xx, EnvInsecureSkipVerify,
		EnvLogLevel, EnvLogFormat,
	}
	for _, v := range envVars {
		os.Unsetenv(v)
	}
	t.Cleanup(func() {
		for _, v := range envVars {
			os.Unsetenv(v)
		}
	})
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && searchString(s, substr)
}

func searchString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}