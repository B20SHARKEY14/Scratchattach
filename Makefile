# Simple Makefile for common tasks

PYTHON ?= /usr/bin/python3
PIP ?= $(PYTHON) -m pip
LOCAL_PACKAGES := .local-packages
REQ := requirements.txt

.PHONY: help install-local venv install-venv run test clean clean-local forget-session create-pth setup-env logout win-build mac-build
.PHONY: install-deps-ubuntu install-deps-mint install-deps-kali install-deps-alpine install-deps-arch install-deps-fedora
.PHONY: run-gui build-gui
.PHONY: build-wheel build-sdist publish build-docker docker-run
.PHONY: help install-local venv install-venv run test clean clean-local forget-session create-pth setup-env run-setup logout win-build mac-build

help:
	@echo "== Scratchattach Makefile =="
	@echo
	@echo "Targets:"
	@echo "  install-local   - install dependencies into $(LOCAL_PACKAGES)"
	@echo "  venv            - create .venv and install dependencies there"
	@echo "  run             - run the app (forwards ARGS to run.sh)"
	@echo "  test            - run tests (pytest or smoke test)"
	@echo "  forget-session  - remove saved session (~/.scratchattach_session)"
	@echo "  clean           - remove .venv and temporary artifacts (preserves $(LOCAL_PACKAGES))"
	@echo "  clean-local     - removes $(LOCAL_PACKAGES) and saved session (use with care)"
	@echo "  setup-env       - interactive .env creation/update (run.setup.sh)"
	@echo "  logout          - remove saved session and clear session env"
	@echo "  win-build       - build MSI using installer/build-msi.ps1 (Windows)"
	@echo "  mac-build       - build macOS .app + DMG using py2app flow"
	@echo "  install-deps-ubuntu - install common OS deps on Ubuntu/Debian-based systems"
	@echo "  install-deps-mint   - install common OS deps on Linux Mint (alias of ubuntu)"
	@echo "  install-deps-kali   - install common OS deps on Kali (alias of ubuntu)"
	@echo "  install-deps-alpine - install common OS deps on Alpine Linux"
	@echo "  install-deps-arch   - install common OS deps on Arch Linux"
	@echo "  install-deps-fedora - install common OS deps on Fedora/RHEL-based systems"

install-local: $(REQ)
	@echo
	@echo "== Installing into $(LOCAL_PACKAGES) =="
	@# Avoid upgrading system pip in constrained environments; install directly into target
	$(PYTHON) -m pip install --target=$(LOCAL_PACKAGES) -r $(REQ)

venv:
	@echo
	@echo "== Creating virtualenv .venv and installing deps =="
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip setuptools wheel
	.venv/bin/python -m pip install -r $(REQ)

install-venv: venv

run:
	@echo
	@echo "== Running ./run.sh $(ARGS) =="
	./run.sh $(ARGS)

test:
	@echo
	@echo "== Running tests =="
	@if command -v pytest >/dev/null 2>&1; then \
		echo "Running pytest..."; pytest -q; \
	else \
		echo "pytest not found, falling back to smoke test"; ./run.sh griffpatch; \
	fi

create-pth:
	@echo
	@echo "== Creating .pth file in user site-packages to point to $(abspath $(LOCAL_PACKAGES)) =="
	@python3 -c 'import site,os,sys; user_site=site.getusersitepackages(); os.makedirs(user_site, exist_ok=True); pth_path=__import__("os").path.join(user_site, "scratchattach_local.pth"); target=__import__("os").path.abspath("$(LOCAL_PACKAGES)"); open(pth_path, "w").write(target+"\n"); print("Wrote", pth_path)'

forget-session:
	@echo
	@echo "== Forgetting saved session (~/.scratchattach_session) =="
	./run.sh --forget-session

clean:
	@echo
	@echo "== Cleaning: remove .venv and temporary artifacts (preserves $(LOCAL_PACKAGES)) =="
	-rm -rf .venv

clean-local:
	@echo
	@echo "== Removing workspace local packages and saved session (use with care) =="
	-rm -rf $(LOCAL_PACKAGES)
	-rm -f ~/.scratchattach_session

setup-env:
	@echo
	@echo "== Interactive .env setup =="
	./run.setup.sh

run-setup:
	@echo
	@echo "== Interactive .env setup (alias run-setup) =="
	./run.setup.sh

logout:
	@echo
	@echo "== Removing saved session and clearing .env session string =="
	./run-logout.sh

win-build:
	@echo
	@echo "== Building MSI (Windows) using installer/build-msi.ps1 =="
	@powershell -NoProfile -ExecutionPolicy Bypass -Command "& './installer/build-msi.ps1' -ProjectDir '$(CURDIR)' -Output 'dist'"

mac-build:
	@echo
	@echo "== Building macOS .app and DMG (py2app flow) =="
	@chmod +x installer/macos/build-app-and-dmg.sh || true
	@./installer/macos/build-app-and-dmg.sh "$(CURDIR)" "$(CURDIR)/dist"
run-gui:
	@echo
	@echo "== Running GUI (pywebview) =="
	@python3 gui.py

build-gui:
	@echo
	@echo "== Build GUI (using pyinstaller) - requires pyinstaller installed =="
	@python3 -m pyinstaller --onefile --windowed gui.py || true

build-wheel:
	@echo
	@echo "== Building wheel and sdist into dist/ (requires 'build' package) =="
	@python3 -m build --outdir dist || true

build-sdist:
	@echo
	@echo "== Building source distribution into dist/ =="
	@python3 -m build --sdist --outdir dist || true

publish:
	@echo
	@echo "== Publish to PyPI (dry-run) =="
	@echo "To publish, install 'twine' and run:"
	@echo "  python3 -m pip install twine"
	@echo "  python3 -m twine upload dist/*"

build-docker:
	@echo
	@echo "== Building Docker image 'scratchattach-helper:latest' =="
	@docker build -t scratchattach-helper:latest .

docker-run:
	@echo
	@echo "== Run scratchattach inside Docker image =="
	@docker run --rm scratchattach-helper:latest fetch griffpatch

# Linux distro helpers: attempt to install common build/runtime deps via each distro's package manager.
# These targets will run package-manager commands and require sudo/root.
SUDO ?= sudo

install-deps-ubuntu:
	@echo
	@echo "== Installing dependencies on Ubuntu/Debian (python3, venv, pip, build tools) =="
	@$(SUDO) apt-get update && $(SUDO) apt-get install -y python3 python3-venv python3-pip build-essential libffi-dev libssl-dev

install-deps-mint: install-deps-ubuntu

install-deps-kali: install-deps-ubuntu

install-deps-alpine:
	@echo
	@echo "== Installing dependencies on Alpine Linux (python3, pip, build-base) =="
	@$(SUDO) apk update && $(SUDO) apk add --no-cache python3 py3-pip build-base libffi-dev openssl-dev

install-deps-arch:
	@echo
	@echo "== Installing dependencies on Arch Linux (python, pip, base-devel) =="
	@$(SUDO) pacman -Syu --noconfirm python python-pip base-devel openssl libffi

install-deps-fedora:
	@echo
	@echo "== Installing dependencies on Fedora (python3, pip, build tools) =="
	@$(SUDO) dnf install -y python3 python3-pip python3-virtualenv gcc make openssl-devel libffi-devel
