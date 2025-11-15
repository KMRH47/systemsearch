.PHONY: install uninstall clean

EXTENSION_DIR := $(HOME)/.local/share/ulauncher/extensions/systemsearch

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
