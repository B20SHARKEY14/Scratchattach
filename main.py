import sys
import os
import json
import argparse

# Try to load environment variables from a .env file if python-dotenv is available
try:
	from dotenv import load_dotenv
	_dotenv_loaded = load_dotenv(os.path.join(os.getcwd(), '.env'))
except Exception:
	_dotenv_loaded = False

# Ensure packages installed into the workspace-local `.local-packages` are importable
local_packages = os.path.join(os.getcwd(), '.local-packages')
if local_packages not in sys.path:
	sys.path.insert(0, local_packages)

import scratchattach
import textwrap
import warnings
try:
	import keyring
	HAVE_KEYRING = True
except Exception:
	HAVE_KEYRING = False
try:
	from rich.console import Console
	from rich.markdown import Markdown
	from rich.panel import Panel
	HAVE_RICH = True
	_console = Console()
except Exception:
	HAVE_RICH = False
	_console = None


def fetch_user_data(username: str) -> dict:
	"""Fetch basic public data for a Scratch username using scratchattach."""
	user = scratchattach.get_user(username)
	ok = user.update()
	if not ok:
		raise RuntimeError(f"Failed to fetch data for user '{username}': {ok}")

	return {
		"id": getattr(user, "id", None),
		"username": getattr(user, "username", None),
		"about_me": getattr(user, "about_me", None),
		"wiwo": getattr(user, "wiwo", None),
		"country": getattr(user, "country", None),
		"icon_url": getattr(user, "icon_url", None),
		"join_date": getattr(user, "join_date", None),
		"scratchteam": getattr(user, "scratchteam", None),
	}


def main():
	parser = argparse.ArgumentParser(description="Retrieve Scratch user data using scratchattach")
	parser.add_argument("--profile", help="Config profile name from ~/.scratchattach/config.toml")
	parser.add_argument("--login-username", help="Username to login with (for authenticated access)")
	parser.add_argument("--login-password", help="Password for login (not recommended on shared shells)")
	parser.add_argument("--session-string", help="Scratch session string to use for authentication")
	parser.add_argument("--browser-login", action="store_true", help="Open browser to login and retrieve session")
	parser.add_argument("--json", action="store_true", help="Print raw JSON output instead of pretty text")
	parser.add_argument("--format", choices=["json", "yaml", "csv", "rich", "pretty"], help="Output format (overrides --json). If not set, human-friendly output is used.")
	parser.add_argument("--export", help="Write output to a file instead of printing (auto-chooses format by extension if not set)")
	parser.add_argument("--debug", action="store_true", help="Enable debug output and warnings")
	parser.add_argument("--forget-session", action="store_true", help="Forget saved session (~/.scratchattach_session) and exit")

	# Subcommands: fetch (default), projects, messages
	subparsers = parser.add_subparsers(dest="command", help="Subcommands")

	sp_fetch = subparsers.add_parser("fetch", help="Fetch user profile data")
	sp_fetch.add_argument("username", nargs="?", help="Scratch username to fetch")

	sp_projects = subparsers.add_parser("projects", help="List projects for a user")
	sp_projects.add_argument("username", nargs="?", help="Scratch username to list projects for")
	sp_projects.add_argument("--limit", type=int, default=20, help="Limit number of projects shown")

	sp_messages = subparsers.add_parser("messages", help="Show message info for a user (auth required)")
	sp_messages.add_argument("username", nargs="?", help="Scratch username to show messages for")

	args = parser.parse_args()

	username = getattr(args, "username", None) or os.environ.get("SCRATCH_USERNAME")
	login_user = args.login_username or os.environ.get("SCRATCH_LOGIN_USERNAME")
	login_pass = args.login_password or os.environ.get("SCRATCH_LOGIN_PASSWORD")
	session_string = args.session_string or os.environ.get("SCRATCH_SESSION_STRING")
	profile_name = args.profile or os.environ.get("SCRATCH_PROFILE")

	# Load optional config file (~/.scratchattach/config.toml) and apply profile defaults
	config = {}
	try:
		# Prefer stdlib tomllib (Python 3.11+)
		import tomllib as _tomllib
		have_toml = True
	except Exception:
		have_toml = False
	if not have_toml:
		try:
			import toml as _tomllib
			have_toml = True
		except Exception:
			have_toml = False

	if have_toml:
		cfg_path = os.path.expanduser("~/.scratchattach/config.toml")
		if os.path.exists(cfg_path):
			try:
				with open(cfg_path, "rb") as f:
					# tomllib requires bytes, toml accepts text
					config = _tomllib.load(f)
			except Exception:
				config = {}

	# If profile specified, merge values into env vars (but keep CLI args precedence)
	if profile_name and isinstance(config, dict):
		prof = config.get(profile_name, {}) if config else {}
		if prof:
			# Only set values if not already provided via CLI or env
			if not username and prof.get("username"):
				username = prof.get("username")
			if not session_string and prof.get("session_string"):
				session_string = prof.get("session_string")
			if not login_user and prof.get("login_username"):
				login_user = prof.get("login_username")
			if not login_pass and prof.get("login_password"):
				login_pass = prof.get("login_password")

	# If user asked to forget the saved session, remove it and exit
	if args.forget_session:
		p = os.path.expanduser("~/.scratchattach_session")
		try:
			if os.path.exists(p):
				os.remove(p)
				print(f"Removed saved session: {p}")
			else:
				print("No saved session found.")
		except Exception as e:
			print("Failed to remove saved session:", e)
		return

	# By default, suppress scratchattach LoginDataWarning unless --debug
	try:
		if not args.debug:
			warnings.filterwarnings('ignore', category=scratchattach.LoginDataWarning)
	except Exception:
		pass

	if not username:
		username = input("Scratch username to fetch: ").strip()

	session = None
	# Try to create an authenticated session if credentials/session provided
	# If no session-string provided, try loading saved session from file
	def session_file_path():
		return os.path.expanduser("~/.scratchattach_session")

	def load_saved_session():
		p = session_file_path()
		if not os.path.exists(p):
			# try keyring as a fallback when enabled
			if HAVE_KEYRING and os.environ.get("SCRATCH_USE_KEYRING") == "1":
				try:
					val = keyring.get_password("scratchattach", "session")
					if val:
						return ("session_string", val)
				except Exception:
					pass
			return None
		try:
			with open(p, "r", encoding="utf-8") as f:
				data = json.load(f)
			# Prefer session_string if present
			if data.get("session_string"):
				return ("session_string", data.get("session_string"))
			if data.get("session_id"):
				return ("session_id", data.get("session_id"), data.get("username"))
		except Exception:
			return None
		return None

	def save_session_info(ses):
		p = session_file_path()
		info = {}
		# Try to get a full session_string first
		try:
			if getattr(ses, "session_string", None):
				info["session_string"] = ses.session_string
		except Exception:
			pass
		# Fallback to session id + username
		try:
			if getattr(ses, "id", None):
				info.setdefault("session_id", ses.id)
			if getattr(ses, "username", None):
				info.setdefault("username", ses.username)
		except Exception:
			pass
		try:
			# write file with restrictive permissions
			umask = os.umask(0)
			with open(p, "w", encoding="utf-8") as f:
				json.dump(info, f)
			os.umask(umask)
			try:
				os.chmod(p, 0o600)
			except Exception:
				pass
			return True
		except Exception:
			return False


		# helper to save into keyring when requested
		def save_session_keyring(session_string):
			if not HAVE_KEYRING:
				return False
			try:
				keyring.set_password("scratchattach", "session", session_string)
				return True
			except Exception:
				return False

	# Attempt to load saved session if user didn't provide one explicitly
	if not session_string and not login_user and not args.browser_login:
		saved = load_saved_session()
		if saved:
			if saved[0] == "session_string":
				session_string = saved[1]
			elif saved[0] == "session_id":
				# emulate passing session id via session_string path
				session_id = saved[1]
				saved_username = saved[2] if len(saved) > 2 else None
				try:
					session = scratchattach.login_by_id(session_id, username=saved_username)
					print("Loaded session from file for:", getattr(session, "username", None))
				except Exception as e:
					print("Failed to load saved session by id:", e)
	if session_string:
		try:
			session = scratchattach.login_by_session_string(session_string)
			# Attempt to refresh session if supported by scratchattach
			try:
				if hasattr(session, "refresh"):
					session.refresh()
			except Exception:
				pass
			print("Logged in via session string as:", getattr(session, "username", None))
		except Exception as e:
			print("Session-string login failed:", e)
	elif login_user and login_pass:
		try:
			session = scratchattach.login(login_user, login_pass)
			# attempt refresh if available
			try:
				if hasattr(session, "refresh"):
					session.refresh()
			except Exception:
				pass
			print("Logged in via username/password as:", getattr(session, "username", None))
		except Exception as e:
			print("Username/password login failed:", e)
	elif args.browser_login:
		try:
			session = scratchattach.login_from_browser()
			# attempt refresh if session exposes it
			try:
				if hasattr(session, "refresh"):
					session.refresh()
			except Exception:
				pass
			print("Logged in via browser as:", getattr(session, "username", None))
		except Exception as e:
			print("Browser login failed:", e)

	# Helper: serialize or write output according to requested format
	def _write_output(obj, fmt=None, export_path=None):
		# Determine format
		fmt = fmt or ("json" if args.json else None)
		if not fmt and export_path:
			if export_path.endswith(".json"):
				fmt = "json"
			elif export_path.endswith(".yaml") or export_path.endswith(".yml"):
				fmt = "yaml"
			elif export_path.endswith(".csv"):
				fmt = "csv"
		# JSON
		if fmt == "json":
			out = json.dumps(obj, indent=2, default=str)
			if export_path:
				with open(export_path, "w", encoding="utf-8") as f:
					f.write(out)
				print(f"Wrote JSON to {export_path}")
				return
			print(out)
			return
		# YAML
		if fmt == "yaml":
			try:
				import yaml
			except Exception:
				print("PyYAML not installed; install 'pyyaml' to use YAML output")
				return
			out = yaml.safe_dump(obj, sort_keys=False)
			if export_path:
				with open(export_path, "w", encoding="utf-8") as f:
					f.write(out)
				print(f"Wrote YAML to {export_path}")
				return
			print(out)
			return
		# CSV: simple heuristics
		if fmt == "csv":
			import csv
			# If top-level is a list of dicts, write table
			if isinstance(obj, list):
				rows = []
				headers = set()
				for item in obj:
					if isinstance(item, dict):
						headers.update(item.keys())
						rows.append(item)
				headers = list(headers)
				if export_path:
					with open(export_path, "w", newline="", encoding="utf-8") as f:
						w = csv.DictWriter(f, fieldnames=headers)
						w.writeheader()
						for r in rows:
							w.writerow({k: v for k, v in r.items()})
					print(f"Wrote CSV to {export_path}")
					return
				w = csv.DictWriter(sys.stdout, fieldnames=headers)
				w.writeheader()
				for r in rows:
					w.writerow({k: v for k, v in r.items()})
				return
			# If dict, write key,value pairs
			if isinstance(obj, dict):
				if export_path:
					with open(export_path, "w", newline="", encoding="utf-8") as f:
						w = csv.writer(f)
						w.writerow(["key", "value"])
						for k, v in obj.items():
							w.writerow([k, v])
					print(f"Wrote CSV to {export_path}")
					return
				w = csv.writer(sys.stdout)
				w.writerow(["key", "value"])
				for k, v in obj.items():
					w.writerow([k, v])
				return
			print("CSV output not available for this data structure")
			return

		# Rich/pretty
		if fmt in ("rich", "pretty") or (fmt is None and not args.json):
			if HAVE_RICH and fmt == "rich":
				# Let existing rich output path handle it (fall-through)
				pass
			if export_path:
				# Fallback to JSON export if exporting pretty text
				with open(export_path, "w", encoding="utf-8") as f:
					f.write(json.dumps(obj, indent=2, default=str))
				print(f"Wrote JSON to {export_path} (pretty export requested)")
				return
			# No export and not JSON: let main pretty-print path handle it (return False)
			return False

	# Handle `projects` subcommand: list projects for the given user (best-effort)
	if getattr(args, "command", None) == "projects":
		if not username:
			username = input("Scratch username to list projects for: ").strip()
		try:
			user = scratchattach.get_user(username)
			ok = user.update()
			if not ok:
				raise RuntimeError(f"Failed to fetch data for user '{username}': {ok}")
			projs = None
			try:
				if hasattr(user, "projects"):
					projs = user.projects()
				elif hasattr(user, "get_projects"):
					projs = user.get_projects()
				else:
					projs = getattr(user, "projects", None)
			except Exception:
				projs = None

			limit = getattr(args, "limit", 20)
			out_obj = {"username": username, "projects": projs}
			# honor requested format/export
			if _write_output(out_obj, fmt=getattr(args, "format", None), export_path=getattr(args, "export", None)) is False:
				# fallback to human output
				if projs:
					print(f"Projects for {username}:")
					n = 0
					for p in projs:
						n += 1
						title = None
						try:
							title = getattr(p, "title", None) or getattr(p, "name", None) or getattr(p, "id", None) or str(p)
						except Exception:
							title = str(p)
						print(f"- {title}")
						if n >= limit:
							break
				else:
					print("No project listing available for this user.")
		except Exception as e:
			print("Error listing projects:", e)
		return

	# Handle `messages` subcommand: requires authentication to show private message info
	if getattr(args, "command", None) == "messages":
		if not username:
			username = input("Scratch username to show messages for: ").strip()
		if session is None:
			print("Messages require an authenticated session. Provide --session-string, --login-username/--login-password, or --browser-login.")
			return
		try:
			user_obj = session.connect_user(username)
			ok = user_obj.update()
			if not ok:
				raise RuntimeError(f"Failed to fetch data for user '{username}': {ok}")
			# Try to show message count and list if available
			msg_count = None
			msgs = None
			try:
				msg_count = user_obj.message_count()
			except Exception:
				msg_count = None
			try:
				if hasattr(user_obj, "messages"):
					msgs = user_obj.messages()
				elif hasattr(user_obj, "get_messages"):
					msgs = user_obj.get_messages()
			except Exception:
				msgs = None

			out_obj = {"username": username, "message_count": msg_count, "messages": msgs}
			if _write_output(out_obj, fmt=getattr(args, "format", None), export_path=getattr(args, "export", None)) is False:
				print(f"Message count: {msg_count}")
				if msgs:
					print("Messages (first 20):")
					for i, m in enumerate(msgs):
						if i >= 20:
							break
						try:
							print(f"- {getattr(m, 'subject', str(m))}")
						except Exception:
							print(f"- {m}")
		except Exception as e:
			print("Error fetching messages:", e)
		return

	try:
		# If we have a session, connect the requested user through it to allow authenticated methods
		if session is not None:
			user_obj = session.connect_user(username)
			ok = user_obj.update()
			if not ok:
				raise RuntimeError(f"Failed to fetch data for user '{username}': {ok}")
			data = {
				**fetch_user_data(username),
				"authenticated_view": True,
				"message_count": None,
			}
			# Try some authenticated-only data (message count) if available
			try:
				data["message_count"] = user_obj.message_count()
			except Exception:
				data["message_count"] = None
			# Save session info for future runs
			try:
				saved_ok = save_session_info(session)
				if saved_ok:
					print("Saved session info to ~/.scratchattach_session")
				# If environment requests keyring usage, try saving session_string there too
				try:
					if HAVE_KEYRING and os.environ.get("SCRATCH_USE_KEYRING") == "1":
						ss = getattr(session, "session_string", None)
						if ss:
							saved_k = save_session_keyring(ss)
							if saved_k:
								print("Saved session into keyring")
				except Exception:
					pass
			except Exception:
				pass
		else:
			data = fetch_user_data(username)

		# Output: either raw JSON or pretty human-readable (with optional rich colors)
		# Try serialization helper first
		if _write_output(data, fmt=getattr(args, "format", None), export_path=getattr(args, "export", None)) is False:
			# helper chose not to serialize; fall back to pretty printing
			if HAVE_RICH:
				c = _console
				c.rule("Scratch user info")
				c.print(Panel.fit(f"[bold cyan]{data.get('username')}[/bold cyan]  (id: {data.get('id')})", title="User"))
				if data.get('about_me'):
					c.print(Panel(textwrap.fill(data.get('about_me'), width=100), title="About"))
				if data.get('wiwo'):
					c.print(Panel(textwrap.fill(data.get('wiwo'), width=100), title="Working on (wiwo)"))
				c.print(f"[green]Country[/green]: {data.get('country')}")
				c.print(f"[green]Join date[/green]: {data.get('join_date')}")
				c.print(f"[green]Scratch Team[/green]: {data.get('scratchteam')}")
				c.print(f"[blue]Icon URL[/blue]: {data.get('icon_url')}")
				if data.get('authenticated_view'):
					c.print(f"[magenta]Message count[/magenta]: {data.get('message_count')}")
				c.rule()
			else:
				# Pretty print selected fields (plain)
				def p(key, value, wrap=80):
					if value is None:
						return
					print(f"{key}:")
					if isinstance(value, str) and ("\n" in value or len(value) > wrap):
						print(textwrap.fill(value, width=wrap))
					else:
						print(value)
					print()

				print("== Scratch user info ==")
				p("Username", data.get("username"))
				p("ID", data.get("id"))
				p("About", data.get("about_me"), wrap=100)
				p("Working on (wiwo)", data.get("wiwo"), wrap=100)
				p("Country", data.get("country"))
				p("Icon URL", data.get("icon_url"))
				p("Join date", data.get("join_date"))
				p("Scratch Team", data.get("scratchteam"))
				if data.get("authenticated_view"):
					p("Message count", data.get("message_count"))
	except Exception as e:
		print("Error:", e)


if __name__ == "__main__":
	main()