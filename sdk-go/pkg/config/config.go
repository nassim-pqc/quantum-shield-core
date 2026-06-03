// Package config provides environment-based configuration for the Quantum Shield Go SDK.
//
// Usage:
//
//	cfg := config.Load()
//	opts := cfg.ClientOptions()
//	client, err := client.New(opts)
package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/quantum-shield/sdk-go/pkg/types"
)

// Config represents the SDK configuration loaded from environment variables.
type Config struct {
	// BaseURL is the Quantum Shield service URL.
	BaseURL string

	// APIKey is the authentication key (X-API-Key header).
	APIKey string

	// Timeout is the HTTP client timeout duration.
	Timeout time.Duration

	// RetryMaxAttempts is the maximum number of retry attempts.
	RetryMaxAttempts int

	// RetryBaseDelay is the base delay between retries (exponential backoff).
	RetryBaseDelay time.Duration

	// RetryOn5xx enables retries on 5xx server errors.
	RetryOn5xx bool

	// InsecureSkipVerify skips TLS certificate verification (dev only).
	InsecureSkipVerify bool

	// LogLevel sets the structured logging level ("debug", "info", "warn", "error").
	LogLevel string

	// LogFormat sets the log output format ("text" or "json").
	LogFormat string
}

// Environment variable names.
const (
	EnvBaseURL            = "QS_URL"
	EnvAPIKey             = "QS_API_KEY"
	EnvTimeout            = "QS_TIMEOUT"
	EnvRetryMaxAttempts   = "QS_RETRY_MAX_ATTEMPTS"
	EnvRetryBaseDelay     = "QS_RETRY_BASE_DELAY"
	EnvRetryOn5xx         = "QS_RETRY_ON_5XX"
	EnvInsecureSkipVerify = "QS_INSECURE_SKIP_VERIFY"
	EnvLogLevel           = "QS_LOG_LEVEL"
	EnvLogFormat          = "QS_LOG_FORMAT"
)

// Default values.
const (
	DefaultBaseURL            = "http://localhost:8000"
	DefaultTimeoutSeconds     = 30
	DefaultRetryMaxAttempts   = 3
	DefaultRetryBaseDelayMS   = 500
	DefaultRetryOn5xx         = true
	DefaultInsecureSkipVerify = false
	DefaultLogLevel           = "info"
	DefaultLogFormat          = "text"
)

// Load reads configuration from environment variables with sensible defaults.
func Load() *Config {
	return &Config{
		BaseURL:            getEnv(EnvBaseURL, DefaultBaseURL),
		APIKey:             getEnv(EnvAPIKey, ""),
		Timeout:            getDuration(EnvTimeout, DefaultTimeoutSeconds, time.Second),
		RetryMaxAttempts:   getInt(EnvRetryMaxAttempts, DefaultRetryMaxAttempts),
		RetryBaseDelay:     getDuration(EnvRetryBaseDelay, DefaultRetryBaseDelayMS, time.Millisecond),
		RetryOn5xx:         getBool(EnvRetryOn5xx, DefaultRetryOn5xx),
		InsecureSkipVerify: getBool(EnvInsecureSkipVerify, DefaultInsecureSkipVerify),
		LogLevel:           getEnv(EnvLogLevel, DefaultLogLevel),
		LogFormat:          getEnv(EnvLogFormat, DefaultLogFormat),
	}
}

// LoadFromMap loads configuration from an arbitrary map (useful for testing).
func LoadFromMap(vars map[string]string) *Config {
	cfg := &Config{
		BaseURL:            valueOr(vars, EnvBaseURL, DefaultBaseURL),
		APIKey:             valueOr(vars, EnvAPIKey, ""),
		Timeout:            parseDuration(valueOr(vars, EnvTimeout, strconv.Itoa(DefaultTimeoutSeconds)), DefaultTimeoutSeconds, time.Second),
		RetryMaxAttempts:   parseInt(valueOr(vars, EnvRetryMaxAttempts, strconv.Itoa(DefaultRetryMaxAttempts)), DefaultRetryMaxAttempts),
		RetryBaseDelay:     parseDuration(valueOr(vars, EnvRetryBaseDelay, strconv.Itoa(DefaultRetryBaseDelayMS)), DefaultRetryBaseDelayMS, time.Millisecond),
		RetryOn5xx:         parseBool(valueOr(vars, EnvRetryOn5xx, "true"), DefaultRetryOn5xx),
		InsecureSkipVerify: parseBool(valueOr(vars, EnvInsecureSkipVerify, "false"), DefaultInsecureSkipVerify),
		LogLevel:           valueOr(vars, EnvLogLevel, DefaultLogLevel),
		LogFormat:          valueOr(vars, EnvLogFormat, DefaultLogFormat),
	}
	return cfg
}

// ClientOptions converts the Config to types.ClientOptions.
func (c *Config) ClientOptions() types.ClientOptions {
	return types.ClientOptions{
		BaseURL:            c.BaseURL,
		APIKey:             c.APIKey,
		Timeout:            c.Timeout,
		RetryMaxAttempts:   c.RetryMaxAttempts,
		RetryBaseDelay:     c.RetryBaseDelay,
		RetryOn5xx:         c.RetryOn5xx,
		InsecureSkipVerify: c.InsecureSkipVerify,
	}
}

// Validate checks the configuration and returns an error if anything is invalid.
func (c *Config) Validate() error {
	if c.BaseURL == "" {
		return fmt.Errorf("%s must not be empty", EnvBaseURL)
	}
	if c.Timeout <= 0 {
		return fmt.Errorf("%s must be positive (got %s)", EnvTimeout, c.Timeout)
	}
	if c.RetryMaxAttempts < 0 {
		return fmt.Errorf("%s must be non-negative (got %d)", EnvRetryMaxAttempts, c.RetryMaxAttempts)
	}
	if c.RetryBaseDelay < 0 {
		return fmt.Errorf("%s must be non-negative (got %s)", EnvRetryBaseDelay, c.RetryBaseDelay)
	}
	return nil
}

// String returns a summary of the configuration (API key is masked).
func (c *Config) String() string {
	key := c.APIKey
	if len(key) > 8 {
		key = key[:4] + "****" + key[len(key)-4:]
	} else if key != "" {
		key = "****"
	}
	return fmt.Sprintf(
		"Config{BaseURL: %s, APIKey: %s, Timeout: %s, RetryMaxAttempts: %d, RetryBaseDelay: %s, RetryOn5xx: %t}",
		c.BaseURL, key, c.Timeout, c.RetryMaxAttempts, c.RetryBaseDelay, c.RetryOn5xx,
	)
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}

func getDuration(key string, fallback int, unit time.Duration) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
		// Try as integer (seconds or the unit's base)
		if i, err := strconv.Atoi(v); err == nil {
			return time.Duration(i) * unit
		}
	}
	return time.Duration(fallback) * unit
}

func getBool(key string, fallback bool) bool {
	if v := os.Getenv(key); v != "" {
		switch v {
		case "true", "1", "yes", "on":
			return true
		case "false", "0", "no", "off":
			return false
		}
	}
	return fallback
}

func valueOr(m map[string]string, key, fallback string) string {
	if v, ok := m[key]; ok {
		return v
	}
	return fallback
}

func parseInt(v string, fallback int) int {
	if i, err := strconv.Atoi(v); err == nil {
		return i
	}
	return fallback
}

func parseDuration(v string, fallback int, unit time.Duration) time.Duration {
	if d, err := time.ParseDuration(v); err == nil {
		return d
	}
	if i, err := strconv.Atoi(v); err == nil {
		return time.Duration(i) * unit
	}
	return time.Duration(fallback) * unit
}

func parseBool(v string, fallback bool) bool {
	switch v {
	case "true", "1", "yes", "on":
		return true
	case "false", "0", "no", "off":
		return false
	}
	return fallback
}