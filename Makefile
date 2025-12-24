# Simple Makefile for common tasks

PYTHON ?= /usr/bin/python3
PIP ?= $(PYTHON) -m pip
LOCAL_PACKAGES := .local-packages
REQ := requirements.txt

.PHONY: help install-local venv install-venv run test clean clean-local forget-session create-pth setup-env logout
.PHONY: help install-local venv install-venv run test clean clean-local forget-session create-pth setup-env run-setup logout

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
