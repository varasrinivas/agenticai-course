"""A stand-in for Ollama's OpenAI-compatible endpoint on :11434.

Every one of the 35 unverified lab scripts reaches the model through exactly one
seam:

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

so a single stub covers all of them. Responses are canned and deterministic,
which is the point: it verifies everything around the model — that the script
imports, builds a well-formed request, handles the tool-call round trip, parses
the reply and prints what its sample claims — without needing a 4GB model or a
paid key, and without the answer text changing between runs.

It deliberately does NOT verify that a real model produces good answers. That
needs Ollama proper. This layer catches the defect classes that actually turned
up in this codebase (a solution importing itself, an LRU evicting the wrong
entry, a sample in the wrong key case) — none of which involved the model.

Run:  python fake_ollama.py            # serves until interrupted
"""
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 11434
CALLS: list[dict] = []          # every request, for assertions afterwards


def canned_reply(body: dict) -> dict:
    """Answer plausibly enough that the script's own parsing is exercised."""
    msgs = body.get("messages", [])
    last = (msgs[-1].get("content") or "") if msgs else ""
    tools = body.get("tools") or []

    # If the script offered tools and hasn't seen a tool result yet, take the
    # tool path — that is the branch most of these labs exist to demonstrate.
    already_ran = any(m.get("role") == "tool" for m in msgs)
    if tools and not already_ran:
        fn = tools[0].get("function", {})
        name = fn.get("name", "unknown_tool")
        props = list((fn.get("parameters") or {}).get("properties", {}))
        args = {p: "test" for p in props[:1]} or {}
        return {
            "id": "chatcmpl-stub", "object": "chat.completion", "created": 0,
            "model": body.get("model", "mistral"),
            "choices": [{
                "index": 0, "finish_reason": "tool_calls",
                "message": {"role": "assistant", "content": None,
                            "tool_calls": [{"id": "call_stub", "type": "function",
                                            "function": {"name": name,
                                                         "arguments": json.dumps(args)}}]},
            }],
            "usage": {"prompt_tokens": 42, "completion_tokens": 7, "total_tokens": 49},
        }

    # If JSON was demanded, return JSON — several labs parse it strictly.
    #
    # Scan every message, not just the last one. The instruction usually lives
    # in the SYSTEM prompt ("Return ONLY a JSON object, no prose") while the last
    # message is the user's data; checking only the last one missed it, the stub
    # answered with prose, and M21C's triage agent correctly rejected it and
    # exited 2. The lab was right and the stub was wrong.
    blob = " ".join(str(m.get("content") or "") for m in msgs)
    wants_json = (body.get("response_format", {}) or {}).get("type") == "json_object" \
        or bool(re.search(r"\bJSON\b", blob, re.I))

    # Honour the shape the prompt spells out, types included. These prompts tend
    # to embed a literal template:
    #
    #   {"anomalies": [{"line": <str>, "severity": "low|medium|high"}],
    #    "clean": <bool>}
    #
    # Filling every field with a string satisfies the key names and still fails:
    # M21C rejected the reply with "'anomalies' must be a list" and exited 2,
    # which is the lab validating correctly against a stub that lied about the
    # type. Read the template and match it.
    def from_template(text: str):
        m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.S)
        if not m:
            return None
        tpl, out = m.group(0), {}
        for key, val in re.findall(r'"(\w+)"\s*:\s*([^,}]+)', tpl):
            v = val.strip()
            if v.startswith("["):
                out[key] = []                       # a list must stay a list
            elif "bool" in v:
                out[key] = True
            elif "|" in v:
                out[key] = v.strip('"<> ').split("|")[0]   # first enum option
            elif re.search(r"\b(int|num|float|count|score)\b", v, re.I):
                out[key] = 1
            elif re.fullmatch(r"-?\d+(\.\d+)?", v.strip('"<> ')):
                # A numeric LITERAL in the template ("overall": 0.0) is the shape
                # too, not a placeholder. Returning "stub" here made M18's judge
                # die on (scores.overall ?? 0).toFixed -- a string satisfied the
                # key and failed the type, which is the same trap as a list.
                out[key] = float(v) if "." in v else int(v)
            else:
                out[key] = "stub"
        return out or None

    shaped = from_template(blob) if wants_json else None
    if shaped is not None:
        content = json.dumps(shaped)
    elif wants_json:
        content = '{"name": "Jane Smith", "email": "jane@acme.com", "company": "Acme Corp"}'
    else:
        content = "This is a deterministic stub response."

    return {
        "id": "chatcmpl-stub", "object": "chat.completion", "created": 0,
        "model": body.get("model", "mistral"),
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 42, "completion_tokens": 9, "total_tokens": 51},
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):        # keep the lab's own stdout readable
        pass

    def _send(self, payload: dict, code: int = 200) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.rstrip("/") in ("/api/tags", "/v1/models"):
            self._send({"models": [{"name": "mistral:latest", "model": "mistral"}],
                        "data": [{"id": "mistral", "object": "model"}]})
        else:
            self._send({"status": "ok"})

    def _send_ndjson(self, objs: list[dict]) -> None:
        """Ollama's native streaming form: one JSON object per line."""
        raw = b"".join((json.dumps(o) + "\n").encode() for o in objs)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._send({"error": "bad json"}, 400)
            return
        CALLS.append({"path": self.path, "model": body.get("model"),
                      "n_messages": len(body.get("messages", [])),
                      "n_tools": len(body.get("tools") or [])})
        # Ollama speaks two protocols and these labs use both: the
        # OpenAI-compatible /v1/... surface (via the `openai` client) and the
        # native /api/chat one (via langchain-ollama and the `ollama` package).
        # The shapes differ — native wraps a single `message`, OpenAI wraps
        # `choices` — so answering the native path in OpenAI shape raises a
        # pydantic ValidationError *inside the lab*, which reads like a lab bug.
        if "/api/chat" in self.path or "/api/generate" in self.path:
            inner = canned_reply(body)["choices"][0]["message"]
            msg = {"role": "assistant", "content": inner.get("content") or ""}
            if inner.get("tool_calls"):
                msg["tool_calls"] = [
                    {"function": {"name": tc["function"]["name"],
                                  "arguments": json.loads(tc["function"]["arguments"])}}
                    for tc in inner["tool_calls"]]
            done = {"model": body.get("model", "mistral"),
                    "created_at": "1970-01-01T00:00:00Z",
                    "message": {"role": "assistant", "content": ""},
                    "done": True, "done_reason": "stop",
                    "prompt_eval_count": 42, "eval_count": 9,
                    "total_duration": 1_000_000}
            if body.get("stream") is False:
                self._send({**done, "message": msg})
            else:
                self._send_ndjson([{**done, "message": msg,
                                    "done": False, "done_reason": None}, done])
        elif "chat/completions" in self.path:
            self._send(canned_reply(body))
        elif "embeddings" in self.path:
            items = body.get("input")
            items = items if isinstance(items, list) else [items]
            self._send({"object": "list", "model": body.get("model", "mistral"),
                        "data": [{"object": "embedding", "index": i,
                                  "embedding": [0.01 * ((i + j) % 97) for j in range(384)]}
                                 for i in range(len(items))],
                        "usage": {"prompt_tokens": 8, "total_tokens": 8}})
        else:
            self._send(canned_reply(body))


def serve() -> HTTPServer:
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    s = serve()
    print(f"stub Ollama listening on http://localhost:{PORT}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        s.shutdown()
        sys.exit(0)
