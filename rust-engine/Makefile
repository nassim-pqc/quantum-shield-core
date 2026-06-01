# ============================================================================
# Quantum Shield Rust Engine — Build automation
# ============================================================================
#
# Targets:
#   build        — Build the Rust library (release)
#   build-debug  — Build the Rust library (debug)
#   test         — Run all unit tests
#   bench        — Run benchmarks
#   python       — Build Python wheel via maturin
#   clean        — Remove build artifacts
#   lint         — Run clippy
#   audit        — Run cargo audit for vulnerabilities
#   docs         — Build documentation
#   check        — Check compilation without building
# ============================================================================

CARGO := cargo
MATURIN := maturin
PYTHON := python3

# Detect if we're in a CI environment
ifdef CI
	CARGO_FLAGS := --verbose
else
	CARGO_FLAGS :=
endif

.PHONY: all build build-debug test bench python clean lint audit docs check

all: build test

# --- Build ---
build:
	$(CARGO) build --release $(CARGO_FLAGS)
	@echo "✅ Rust engine built (release)"

build-debug:
	$(CARGO) build $(CARGO_FLAGS)
	@echo "✅ Rust engine built (debug)"

# --- Tests ---
test:
	$(CARGO) test $(CARGO_FLAGS)
	@echo "✅ All Rust tests passed"

# --- Benchmarks ---
bench:
	$(CARGO) bench $(CARGO_FLAGS)
	@echo "✅ Benchmarks complete"

# --- Python wheel (PyO3) ---
python:
	$(MATURIN) build --release --features python-bindings
	@echo "✅ Python wheel built"

python-install: python
	$(MATURIN) develop --features python-bindings
	@echo "✅ Python wheel installed (maturin develop)"

# --- Clean ---
clean:
	$(CARGO) clean
	rm -rf target/
	rm -rf *.egg-info/
	@echo "✅ Build artifacts cleaned"

# --- Lint ---
lint:
	$(CARGO) clippy --all-targets --all-features -- -D warnings
	@echo "✅ Clippy lint passed"

# --- Security audit ---
audit:
	$(CARGO) audit
	@echo "✅ Cargo audit passed"

# --- Documentation ---
docs:
	$(CARGO) doc --no-deps --document-private-items
	@echo "✅ Documentation built (target/doc/)"

# --- Check compilation ---
check:
	$(CARGO) check --all-targets --all-features $(CARGO_FLAGS)
	@echo "✅ Compilation check passed"

# --- Full CI pipeline ---
ci: check lint test bench

# --- Generate Cargo.lock (needed for SBOM) ---
lockfile:
	$(CARGO) generate-lockfile
	@echo "✅ Cargo.lock generated"