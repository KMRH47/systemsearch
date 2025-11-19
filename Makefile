.PHONY: install uninstall clean test help %

MAKEFLAGS += --no-print-directory --silent
.SILENT:
EXTENSION_DIR := $(HOME)/.local/share/ulauncher/extensions/systemsearch

# Helper to create a space character variable for substitution
null :=
space := $(null) $(null)

# 1. Filter out 'test' to get arguments
# 2. Replace spaces with slashes (e.g., "macos extension" -> "macos/extension")
ARGS := $(filter-out test,$(MAKECMDGOALS))
TEST_PATH := $(subst $(space),/,$(ARGS))

help:
	@echo "Available targets:"
	@echo "  make install    - Install the extension"
	@echo "  make uninstall  - Uninstall the extension"
	@echo "  make clean      - Clear frequency cache"
	@echo "  make test       - Run all tests"
	@echo "  make test <dir> - Run tests in specific directory (e.g., make test linux ulauncher)"
	@echo ""
	@echo "Run specific tests:"
	@echo "  python3 linux/ulauncher/tests/test_frequency.py      - Run frequency tests"
	@echo "  python3 linux/ulauncher/tests/test_search_unit.py    - Run search unit tests"
	@echo "  python3 linux/ulauncher/tests/test_search.py         - Run integration tests"

install:
	@if ! command -v plocate >/dev/null 2>&1; then \
		echo "Installing plocate..."; \
		sudo apt-get update -qq && sudo apt-get install -y -qq plocate; \
	fi
	@mkdir -p $(EXTENSION_DIR)
	@cp -r linux/ulauncher/* $(EXTENSION_DIR)/
	@pkill -9 ulauncher 2>/dev/null || true
	@sleep 1
	@ulauncher >/dev/null 2>&1 &
	@echo "systemsearch installed! Open Ulauncher and type 'find <query>'"

uninstall:
	@rm -rf $(EXTENSION_DIR)
	@rm -f $(HOME)/.cache/ulauncher-systemsearch-frequency.json
	@echo "Uninstalled systemsearch"

clean:
	@rm -f $(HOME)/.cache/ulauncher-systemsearch-frequency.json
	@echo "Cleared frequency cache"

test:
	@target="$(TEST_PATH)"; \
	if [ -z "$$target" ]; then target="."; fi; \
	python3 scripts/run-tests.py "$$target"

# Catch-all to prevent errors for arguments treated as targets
%:
	@:

