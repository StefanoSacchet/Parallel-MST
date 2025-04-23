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

# ONLY FOR HPC

load-modules:
	@echo "Loading modules..."
	./load_modules.sh

# submit:
# 	@echo "Submitting job..."
# 	./run_hpc.sh

monitor:
	@watch "qstat -u $(USER)"

cancel-jobs:
	@echo "Canceling all jobs..."
	@for job in `qstat -u $(USER) | grep "hpc-hea" | awk '{print $$1}' | cut -d'.' -f1`; do \
		echo "Canceling job $$job"; \
		qdel $$job; \
	done

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  release            Build the project in release mode"
	@echo "  debug              Build the project in debug mode"
	@echo "  clean              Clean the build directory"
	@echo "  format             Format the source code using clang-format"
	@echo "  check-formatting-deps Check if clang-format is installed"
	@echo "  test               Run tests and generate"
	@echo "  load-modules       Load necessary modules for HPC"
	@echo "  submit             Submit a job to the HPC queue"
	@echo "  monitor            Monitor the status of submitted jobs"
	@echo "  cancel-jobs        Cancel all submitted jobs"

