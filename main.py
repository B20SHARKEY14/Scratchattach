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
	parser.add_argument("username", nargs="?", help="Scratch username to fetch")
	parser.add_argument("--login-username", help="Username to login with (for authenticated access)")
	parser.add_argument("--login-password", help="Password for login (not recommended on shared shells)")
	parser.add_argument("--session-string", help="Scratch session string to use for authentication")
	parser.add_argument("--browser-login", action="store_true", help="Open browser to login and retrieve session")
	parser.add_argument("--json", action="store_true", help="Print raw JSON output instead of pretty text")
	parser.add_argument("--debug", action="store_true", help="Enable debug output and warnings")
	parser.add_argument("--forget-session", action="store_true", help="Forget saved session (~/.scratchattach_session) and exit")
	args = parser.parse_args()

	username = args.username or os.environ.get("SCRATCH_USERNAME")
	login_user = args.login_username or os.environ.get("SCRATCH_LOGIN_USERNAME")
	login_pass = args.login_password or os.environ.get("SCRATCH_LOGIN_PASSWORD")
	session_string = args.session_string or os.environ.get("SCRATCH_SESSION_STRING")

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
			print("Logged in via session string as:", getattr(session, "username", None))
		except Exception as e:
			print("Session-string login failed:", e)
	elif login_user and login_pass:
		try:
			session = scratchattach.login(login_user, login_pass)
			print("Logged in via username/password as:", getattr(session, "username", None))
		except Exception as e:
			print("Username/password login failed:", e)
	elif args.browser_login:
		try:
			session = scratchattach.login_from_browser()
			print("Logged in via browser as:", getattr(session, "username", None))
		except Exception as e:
			print("Browser login failed:", e)

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
			except Exception:
				pass
		else:
			data = fetch_user_data(username)

		# Output: either raw JSON or pretty human-readable (with optional rich colors)
		if args.json:
			print(json.dumps(data, indent=2))
		else:
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