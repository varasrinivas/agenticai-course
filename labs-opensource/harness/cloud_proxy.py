"""Forward :11434 to a real Ollama, swapping the model name on the way through.

Why this exists
---------------
Every lab hardcodes `model="mistral"` and `base_url="http://localhost:11434/v1"`.
On a CPU-only machine mistral costs about 40 seconds per call, which puts a full
`--live` sweep into the hours and makes the long multi-call labs (ReAct,
planning, multi-agent) effectively unrunnable.

Ollama's cloud models answer through the same local endpoint in about 1.5
seconds, but Ollama publishes no cloud build of mistral. Running the labs
against cloud therefore means running them against a *different* model.

The tempting shortcut is `ollama cp gpt-oss:20b-cloud mistral`, so the labs
"just work" unchanged. Do not: every later run, and every log, would say
"mistral" while executing something else. A verification harness that
misreports what it tested is worse than no harness.

So the substitution is made explicit instead. This proxy sits on 11434, sends
everything to a real Ollama on another port, and rewrites the model field --
loudly, in its banner and in the results it enables.

What a pass here does and does not mean
---------------------------------------
It DOES show the lab's code is sound: it builds valid requests, survives the
tool-call round trip, parses replies, and completes against a real LLM.

It does NOT show the lab works *as shipped*. A prompt that a 20B model handles
may defeat mistral 7B -- strict JSON, tool-call formatting and loop termination
are exactly where a smaller model gives out. Results obtained through this proxy
must be labelled with the model that actually served them, never as "mistral".

Usage:
    # terminal 1 -- real Ollama on a spare port
    OLLAMA_HOST=127.0.0.1:11435 ollama serve

    # terminal 2
    python harness/cloud_proxy.py --to 11435 --model gpt-oss:20b-cloud

    # terminal 3
    python harness/run_labs.py --live --resume
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

LISTEN = 11434
UPSTREAM = 11435
SUBSTITUTE = "gpt-oss:20b-cloud"
SWAPPED = 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _relay(self, method: str) -> None:
        global SWAPPED
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""

        # Only chat traffic is rewritten. An embedding request routed to a chat
        # model does not fail cleanly -- it stalls or returns something that is
        # not a vector -- and the substitute is a chat model. Embedding calls go
        # upstream untouched, so they keep using whatever the lab asked for.
        is_embedding = "embed" in self.path.lower()

        if raw and not is_embedding:
            try:
                body = json.loads(raw)
                if isinstance(body, dict) and "model" in body:
                    if body["model"] != SUBSTITUTE:
                        SWAPPED += 1
                    body["model"] = SUBSTITUTE
                    raw = json.dumps(body).encode()
            except json.JSONDecodeError:
                pass                     # not JSON: pass it through untouched

        url = f"http://127.0.0.1:{UPSTREAM}{self.path}"
        req = urllib.request.Request(url, data=raw or None, method=method)
        for k, v in self.headers.items():
            if k.lower() not in ("host", "content-length", "connection"):
                req.add_header(k, v)
        if raw:
            req.add_header("Content-Length", str(len(raw)))

        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                payload, code = resp.read(), resp.status
                ctype = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:          # relay upstream errors verbatim
            payload, code = e.read(), e.code
            ctype = e.headers.get("Content-Type", "application/json")
        except Exception as e:                        # upstream down / timed out
            payload = json.dumps({"error": f"proxy upstream failed: {e}"}).encode()
            code, ctype = 502, "application/json"

        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._relay("GET")

    def do_POST(self):
        self._relay("POST")


def main() -> int:
    global UPSTREAM, SUBSTITUTE
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", type=int, default=UPSTREAM, help="port the real Ollama listens on")
    ap.add_argument("--model", default=SUBSTITUTE, help="model to substitute for whatever is requested")
    args = ap.parse_args()
    UPSTREAM, SUBSTITUTE = args.to, args.model

    try:
        srv = HTTPServer(("127.0.0.1", LISTEN), Handler)
    except OSError as exc:
        print(f"cannot bind {LISTEN}: {exc}\n"
              f"Move the real Ollama aside first: OLLAMA_HOST=127.0.0.1:{UPSTREAM} ollama serve",
              file=sys.stderr)
        return 2

    print(f"proxy :{LISTEN} -> :{UPSTREAM}", flush=True)
    print(f"REWRITING every requested model to {SUBSTITUTE!r} — results from this "
          f"session are NOT evidence about mistral", flush=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
