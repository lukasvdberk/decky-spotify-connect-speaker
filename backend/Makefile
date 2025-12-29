# Makefile for building spotifyd from Arch Linux package

# Arch package details (using archive.archlinux.org for reliability)
SPOTIFYD_PKG = spotifyd-0.4.2-1-x86_64.pkg.tar.zst
SPOTIFYD_URL = https://archive.archlinux.org/packages/s/spotifyd/$(SPOTIFYD_PKG)

# Output directory for binaries (will be copied to plugin bin/ folder)
OUT_DIR = ./out

.PHONY: all
all: spotifyd

# Download and extract spotifyd from Arch package
spotifyd:
	mkdir -p $(OUT_DIR)
	mkdir -p ./tmp
	@echo "Downloading spotifyd from Arch Linux..."
	curl -L -o ./tmp/$(SPOTIFYD_PKG) $(SPOTIFYD_URL)
	@echo "Extracting spotifyd binary..."
	cd ./tmp && tar --use-compress-program=unzstd -xf $(SPOTIFYD_PKG) usr/bin/spotifyd
	cp ./tmp/usr/bin/spotifyd $(OUT_DIR)/spotifyd
	chmod +x $(OUT_DIR)/spotifyd
	rm -rf ./tmp
	@echo "spotifyd binary extracted to $(OUT_DIR)/spotifyd"

.PHONY: clean
clean:
	rm -rf $(OUT_DIR) ./tmp
