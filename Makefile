MAKEFLAGS += --no-print-directory
CORES = $(shell nproc)

.PHONY: release debug clean format check-formatting-deps

define setup_folder
	if [ -d bin ]; then \
		if [ ! -f .last_compilation_mode ] || [ "$$(cat .last_compilation_mode | sed 's/^ *//;s/ *$$//')" != "$$(echo $(1) | sed 's/^ *//;s/ *$$//')" ]; then \
			echo "File content '$$(cat .last_compilation_mode)' differs from '$(1)' (after trimming spaces)"; \
			echo "===> removing binaries\n"; \
			rm -r bin; \
		fi; \
	fi; \
	mkdir -p $(1); \
	echo $(1) > .last_compilation_mode; \
	cd $(1);
endef

debug:
	@$(call setup_folder, build/debug) \
 	cmake ../.. -DCMAKE_BUILD_TYPE=Debug; \
	make -j$(CORES);

release:
	@$(call setup_folder, build/release) \
	cmake ../.. -DCMAKE_BUILD_TYPE=Release; \
	make -j$(CORES);

clean:
	@if [ -d build ]; then \
		echo "removing build folder"; \
		rm -r build;\
	fi

format:
	@find ./src/ -name "*.c" -o -name "*.h" | xargs clang-format -style=file:.clang-format -i

check-formatting-deps:
	@which clang-format >/dev/null 2>&1 || { \
		echo "Error: clang-format is not installed. Please install it:"; \
		echo "  - On Ubuntu: sudo apt install clang-format"; \
		echo "  - On macOS: brew install clang-format"; \
		exit 1; \
	}

test: debug
	@set -e; \
	$(call setup_folder, build/debug) \
 	cmake ../.. -DCMAKE_BUILD_TYPE=Debug; \
	make -j$(CORES) test_all; \
	ctest --output-on-failure; \
	cd -;
