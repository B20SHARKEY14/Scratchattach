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

Config profiles (optional)
--------------------------

For convenience you can store multiple named profiles in a TOML config file at `~/.scratchattach/config.toml`.
The CLI supports `--profile NAME` or the `SCRATCH_PROFILE` environment variable to select a profile.

Create `~/.scratchattach/config.toml` with sections for each profile, for example:

```toml
[default]
username = "griffpatch"
# session_string = "SESSION_STRING_HERE"
# login_username = "you"
# login_password = "secret"

[work]
username = "yourworkuser"
session_string = ""
```

When a profile is selected, fields from the profile are used only when the same value is not
provided on the command-line or via the `.env`/environment variables.

An example config template is included as `config.example.toml` in the repository.

CLI subcommands
---------------

The tool now offers three subcommands for focused workflows:

- `fetch`: fetch a user's public profile (default fields).
- `projects`: list a user's projects (best-effort; depends on library support).
- `messages`: show message info for a user (requires authentication).

Examples:

```bash
make run ARGS="fetch griffpatch"
make run ARGS="projects griffpatch --limit 10"
make run ARGS="messages griffpatch --session-string \"$SCRATCH_SESSION_STRING\""
```

If no subcommand is given, the previous positional-style usage is still supported for backward compatibility.

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

MSI installer
-------------
I added a WiX-based installer definition and a GitHub Actions workflow that builds an MSI on
Windows runners. The workflow is at `.github/workflows/build-msi.yml` and uses the WiX source
at `installer/installer.wxs`.

To build locally on Windows you can run (requires WiX Toolset):

```powershell
choco install wixtoolset -y
powershell .\installer\build-msi.ps1 -ProjectDir . -Output .\dist
```

Or trigger the workflow on GitHub and download the `scratchattach-msi` artifact from the run.

Notes:
- The MSI created by the workflow simply copies repository files into `Program Files\Scratchattach`.
- You may want to customize the WiX source (`installer/installer.wxs`) to add shortcuts, registry
	entries, or to include a packaged Python runtime.

Alternatively, on systems with PowerShell available you can run the Makefile helper:

```bash
make win-build
```

Using the MSI
-------------
- The generated MSI installs files under `C:\Program Files\Scratchattach` by default and
	requires admin privileges. Run the MSI and follow the Windows installer UI to install.
- After installation you can run the packaged `main.py` with the system Python, or open a
	Command Prompt and run the launcher script if you included it in the MSI target folder.

Build notes and customization
-----------------------------
- The WiX source in `installer/installer.wxs` contains placeholder GUIDs (`PUT-GUID-*`) and an
	`UpgradeCode` placeholder; replace these with stable GUIDs for production builds.
- To make the MSI self-contained you can bundle an embeddable Python distribution or a
	pre-built portable interpreter into the installer and adjust `installer.wxs` to place it
	into the install folder and update launcher scripts to use the embedded Python.
- For automated CI builds we install WiX via Chocolatey on the runner; building locally may
	require admin rights.

Linux distributions
-------------------

This project provides convenience Makefile helpers to install common runtime/build dependencies
on several Linux distributions. These targets run the distribution package manager and require
`sudo` (or root) to install packages.

- Ubuntu / Debian / Linux Mint / Kali:

	```bash
	make install-deps-ubuntu
	# or
	make install-deps-mint
	make install-deps-kali
	```

	These targets run `apt-get` to install `python3`, `python3-venv`, `python3-pip`, `build-essential`,
	`libssl-dev`, and `libffi-dev`.

- Fedora / RHEL:

	```bash
	make install-deps-fedora
	```

	Uses `dnf` to install `python3`, `python3-pip` and common build dependencies.

- Arch Linux:

	```bash
	make install-deps-arch
	```

	Uses `pacman` to install `python`, `python-pip`, `base-devel`, `openssl`, and `libffi`.

- Alpine Linux:

	```bash
	make install-deps-alpine
	```

	Uses `apk` to install `python3`, `py3-pip`, `build-base`, `libffi-dev`, and `openssl-dev`.

Notes
-----
- These Makefile targets are convenience helpers — review the commands before running them on
	production systems.
- On systems without `sudo`, run the underlying package manager commands as root.
- If you prefer containerized builds, consider running the project inside a distro-specific
	container (Docker/Podman) rather than modifying the host system.

macOS installer
---------------
This repo includes two macOS build flows:

- Simple DMG packager: `installer/macos/build-dmg.sh` — packages repository files into a compressed
	DMG with an Applications symlink. Use this for quick sharing of files.

- py2app-based app + DMG: builds a standalone macOS `.app` from `main.py` using `py2app`, then
	packages the `.app` into a DMG. The script is `installer/macos/build-app-and-dmg.sh` and the
	workflow `.github/workflows/build-mac.yml` now runs this script on `macos-latest`.

To build locally with the py2app flow (macOS):

```bash
chmod +x installer/macos/build-app-and-dmg.sh
./installer/macos/build-app-and-dmg.sh /path/to/project /path/to/output
```

What it does:

- Creates a temporary virtualenv, installs `py2app` and packages listed in `requirements.txt`.
- Runs `setup_py2app.py` to build `dist/main.app`.
- Packages the `.app` into a compressed DMG with an Applications symlink for drag-and-drop.

Notes and next steps:

- The `.app` built by `py2app` bundles your Python code and installed libraries, but not the
	system Python itself; the app will include an embedded Python interpreter provided by py2app.
- This script does not perform code signing or notarization — add macOS signing and notarization
	steps if you intend to distribute the app publicly (requires an Apple Developer account).

You can also use the Makefile helper on macOS runners or machines with bash:

```bash
make mac-build
```
- For more polished macOS installers consider using `py2app` plus a branded `.app` bundle, adding
	an icon, and signing/notarizing in CI.

Using the macOS app and DMG
--------------------------
- The py2app build produces `dist/main.app` inside the project; the DMG builder packages that
	`.app` into a compressed `Scratchattach.dmg` that users can mount and drag the app into
	`/Applications`.
- To run the app locally after building, double-click the `.app` bundle or run the contained
	executable from the terminal, e.g. `open dist/main.app`.

Signing and notarization
------------------------
- The build scripts do not sign or notarize the app; unsigned apps will trigger Gatekeeper on
	end-user systems. For distribution you should sign the `.app` and then notarize with Apple.
	This requires an Apple Developer account and access to signing keys. CI can be extended to
	perform signing and notarization using `altool`/`notarytool` with secrets stored in GitHub.
