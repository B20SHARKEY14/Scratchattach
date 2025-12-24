import sys
import os
import threading
import json

# ensure local packages on sys.path
local_packages = os.path.join(os.getcwd(), '.local-packages')
if local_packages not in sys.path:
    sys.path.insert(0, local_packages)

try:
    import webview
except Exception:
    webview = None

try:
    import scratchattach
except Exception:
    scratchattach = None

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Scratchattach GUI</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 1rem; }
      input, button { font-size: 1rem; }
      #out { white-space: pre-wrap; margin-top: 1rem; border: 1px solid #ddd; padding: 0.5rem; height: 60vh; overflow: auto; }
    </style>
  </head>
  <body>
    <h2>Scratchattach GUI</h2>
    <div>
      <label>Username: <input id="username" /></label>
      <button onclick="window.pyfetch()">Fetch</button>
    </div>
    <div id="out">Ready.</div>
    <script>
      function setOut(s){ document.getElementById('out').textContent = s }
      window.setOut = setOut
    </script>
  </body>
</html>
"""

class Api:
    def __init__(self, window):
        self.window = window

    def pyfetch(self):
        # called from JS when user clicks Fetch
        username = self.window.evaluate_js("document.getElementById('username').value")
        if not username:
            self.window.evaluate_js("setOut('Please enter a username')")
            return
        self.window.evaluate_js("setOut('Fetching...')")

        def work():
            try:
                if scratchattach is None:
                    out = 'scratchattach not available. Install requirements.'
                else:
                    user = scratchattach.get_user(username)
                    ok = user.update()
                    if not ok:
                        out = f'Failed to fetch user: {ok}'
                    else:
                        data = {
                            'id': getattr(user, 'id', None),
                            'username': getattr(user, 'username', None),
                            'about_me': getattr(user, 'about_me', None),
                            'wiwo': getattr(user, 'wiwo', None),
                            'country': getattr(user, 'country', None),
                            'join_date': getattr(user, 'join_date', None),
                        }
                        out = json.dumps(data, indent=2)
            except Exception as e:
                out = f'Error: {e}'
            # send back to page
            try:
                self.window.evaluate_js(f"setOut({json.dumps(out)})")
            except Exception:
                pass

        t = threading.Thread(target=work, daemon=True)
        t.start()


def main():
    if webview is None:
        print('pywebview not installed; run `pip install pywebview` or make install-local`')
        return
    window = webview.create_window('Scratchattach', html=HTML, width=800, height=600)
    api = Api(window)
    webview.start(func=None, gui='qt', http_server=False, debug=False, api=api)

if __name__ == '__main__':
    main()
