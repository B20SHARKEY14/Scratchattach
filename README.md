# Scratchattach

## Installation (workspace-local)

To avoid modifying the system Python, install `scratchattach` into a workspace-local directory and add that directory to `PYTHONPATH` or `sys.path`.

1. Install into `.local-packages`:

```bash
/usr/bin/python3 -m pip install --target=.local-packages scratchattach
```

2a. Run scripts using `PYTHONPATH` from the shell:

```bash
PYTHONPATH=.local-packages /usr/bin/python3 your_script.py
```

2b. Or add the local-packages directory at runtime in Python:

```python
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), '.local-packages'))
import scratchattach
```

Notes:

If you want, I can add a small example to `main.py` showing a basic `scratchattach` import and version print.

## Authenticated usage and running

The `main.py` script supports optional authentication so it can access private endpoints (messages, etc.).


```bash
PYTHONPATH=.local-packages /usr/bin/python3 main.py griffpatch --session-string "$SCRATCH_SESSION_STRING"
```


```bash
PYTHONPATH=.local-packages /usr/bin/python3 main.py griffpatch --login-username you --login-password secret
```


```bash
PYTHONPATH=.local-packages /usr/bin/python3 main.py griffpatch --browser-login
```

# Scratchattach

This repo contains a small helper (`main.py`) that demonstrates using the `scratchattach` library
to fetch public and (optionally) authenticated Scratch account data.

Quickstart
---------
- Install runtime dependencies into a workspace-local folder (recommended):

```bash
make install-local
```

- Or create a virtual environment and install:

```bash
make venv
```

- Create a `.pth` so `.local-packages` is automatically available in Python (optional):

```bash
make create-pth
# Scratchattach

This repository contains a small helper (`main.py`) that demonstrates using the `scratchattach`
library to fetch public and (optionally) authenticated Scratch account data. The project also
provides convenient scripts and Makefile targets to keep workspace-local installs and secrets
separated from the system Python.

Quickstart (preferred: Makefile)
--------------------------------
1. Install runtime dependencies into a workspace-local folder (recommended):

```bash
make install-local
```

2. Create a `.pth` so `.local-packages` is automatically available in Python (optional):

```bash
make create-pth
```

3. Run the helper (preferred via Makefile):

```bash
make run ARGS="griffpatch"
```

Fallback: you can also run the launcher script directly if needed:

```bash
./run.sh griffpatch
```

Environment and authentication
------------------------------
- `make setup-env` (or the alias `make run-setup`) launches an interactive helper that creates or updates
	a `.env` file with common environment variables. It prompts for these values (press Enter to keep
	an existing value or leave blank):

	- `SCRATCH_SESSION_STRING`
	- `SCRATCH_LOGIN_USERNAME`
	- `SCRATCH_LOGIN_PASSWORD`
	- `SCRATCH_USERNAME`

	The helper runs `./run.setup.sh` and writes `.env` with restrictive permissions when possible.

	Example (run interactively):

	```bash
	make setup-env
	# or
	make run-setup
	```

	Non-interactive option (advanced): copy values into `.env` or export them in your shell before running `make run`.

- To login or run with authentication, prefer Makefile usage (examples):

```bash
make run ARGS="griffpatch --session-string \"$SCRATCH_SESSION_STRING\""
make run ARGS="griffpatch --login-username you --login-password secret"
make run ARGS="griffpatch --browser-login"
```

Fallback script forms:

```bash
./run.sh griffpatch --browser-login
```

Session persistence and logout
------------------------------
- After a successful login the tool saves a small session file at `~/.scratchattach_session`.
- To forget the saved session and clear the session entry in `.env`, use the Makefile target:

```bash
make logout
```

or the script fallback:

```bash
./run-logout.sh
```

Development, tests and maintenance
---------------------------------
- Create a virtualenv (alternative to `install-local`):

```bash
make venv
```

- Run tests:

```bash
make test
tox
```

- Cleaning:
	- `make clean` — removes `.venv` and temporary artifacts but preserves `.local-packages`.
	- `make clean-local` — removes `.local-packages` and the saved session (use with care).

Notes
-----
- Local packages are installed into `.local-packages` (ignored by git).
- Colored output is available when `rich` is installed (listed in `requirements.txt`).
- Do not commit `.env` or `~/.scratchattach_session` to source control.

If you'd like, I can add a GitHub Actions workflow to run `make test` on push/pull requests.
