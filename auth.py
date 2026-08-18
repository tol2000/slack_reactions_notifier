import os
import sys
import json
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# Read temporary app credentials from the user's terminal session
CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "")
PORT = 8000
REDIRECT_URI = f"http://localhost:{PORT}"

if not CLIENT_ID or not CLIENT_SECRET:
    print("CRITICAL ERROR: Missing mirror app credentials!", file=sys.stderr)
    print("Please set SLACK_CLIENT_ID and SLACK_CLIENT_SECRET environment variables before running.", file=sys.stderr)
    sys.exit(1)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        # Fully mute default HTTP server console noise safely
        return

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if "code" not in query_params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed: No OAuth code returned from Slack.")
            return

        auth_code = query_params["code"][0]

        # Exchange temporary code for secure tokens via official Slack API
        token_url = "https://slack.com"
        data = urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI
        }).encode("utf-8")

        req = urllib.request.Request(token_url, data=data, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))

                if not res_data.get("ok"):
                    error_msg = res_data.get('error', 'Unknown error')
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(f"Slack API Error: {error_msg}".encode("utf-8"))
                    return

                # Extract secure user tokens and personal member id
                user_token = res_data.get("authed_user", {}).get("access_token")
                user_id = res_data.get("authed_user", {}).get("id")

                # Fallback print to the console
                print("\n" + "=" * 60)
                print("🎉 TOKENS SUCCESSFULLY ACQUIRED!")
                print(f"SLACK_USER_TOKEN={user_token}")
                print(f"MY_SLACK_ID={user_id}")
                print("=" * 60 + "\n")

                # Generate clean and modern output UI for the user's browser
                html_response = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Slack Tokens Acquired</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; background-color: #f8f9fa; color: #333; }}
                        .container {{ max-width: 600px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin: 40px auto; }}
                        h1 {{ color: #2eb67d; margin-top: 0; font-size: 24px; }}
                        p {{ color: #4a5568; font-size: 15px; margin-bottom: 25px; }}
                        .token-box {{ background: #f1f3f5; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin: 8px 0 20px 0; font-family: monospace; font-size: 14px; word-break: break-all; user-select: all; }}
                        label {{ font-weight: bold; color: #2d3748; display: block; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
                        .note {{ font-size: 13px; color: #718096; margin-top: 25px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Success! 🎉</h1>
                        <p>Your private mirror application has been successfully authorized. Copy the two variables below and add them to your production <code>.env</code> file:</p>

                        <label>SLACK_USER_TOKEN</label>
                        <div class="token-box">{user_token}</div>

                        <label>MY_SLACK_ID</label>
                        <div class="token-box">{user_id}</div>

                        <p class="note">💡 <b>Next steps:</b> You can double-click inside boxes to copy values. Once copied, close this browser tab and the script in your terminal will terminate automatically.</p>
                    </div>
                </body>
                </html>
                """

                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_response.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Local server error during token exchange: {e}".encode("utf-8"))

        # Shutdown the ephemeral server after sending the response page
        raise KeyboardInterrupt


def run_local_server():
    server = HTTPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
    scopes = "reactions:read,channels:history,groups:history"
    slack_auth_url = f"https://slack.com{CLIENT_ID}&user_scope={scopes}&redirect_uri={REDIRECT_URI}"

    print(f"Starting ephemeral local authentication server on port {PORT}...")
    print(f"Opening your browser for Slack authentication...")
    print(f"If the browser doesn't open automatically, please visit:\n{slack_auth_url}")

    webbrowser.open(slack_auth_url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\nLocal CLI authentication server stopped safely.")


if __name__ == "__main__":
    run_local_server()
