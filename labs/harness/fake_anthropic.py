"""A stand-in for api.anthropic.com, for running the Claude labs offline.

The Ollama course could be verified for free because its model runs locally.
This course cannot: its labs call a paid API, so every run costs money and
returns something different. That is a poor fit for a check you want to run on
every change, and it is why these 49 scripts stayed unverified while the Ollama
ones did not.

Every lab here builds its client the same way:

    client = anthropic.Anthropic()

which reads ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL from the environment. So
pointing the whole course at a local stub needs no proxy and no edits -- just
two environment variables, which is what run_labs.py sets.

What this proves, and what it does not
--------------------------------------
It proves the lab's code is sound: it constructs a valid request, handles the
tool-use round trip, reads content blocks and stop_reason correctly, and runs
to completion.

It proves nothing about Claude's answers. Replies here are canned. A lab whose
point is answer quality -- an eval, a judge, a guardrail decision -- will pass
against this stub while being wrong in production. Those need a real key, and
the README says which they are.

Serves the subset of the Messages API the labs actually use:
  POST /v1/messages          text, tool_use, and stop_reason handling
  POST /v1/messages/count_tokens
"""
from __future__ import annotations

import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8787
CALLS: list[dict] = []


def _text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def canned_message(body: dict) -> dict:
    """Answer in the shape the SDK expects, exercising the branch the lab is in."""
    msgs = body.get("messages", [])
    tools = body.get("tools") or []

    # A lab that sent tool_results is on its second leg and wants prose now;
    # answering with another tool_use would spin it forever.
    already_ran = any(
        isinstance(m.get("content"), list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
        for m in msgs
    )

    if tools and not already_ran:
        tool = tools[0]
        schema = tool.get("input_schema") or {}
        props = schema.get("properties", {}) or {}
        required = schema.get("required") or list(props)[:1]

        # Synthesise arguments from the schema rather than sending a constant.
        # A tool given a value outside its enum takes its error branch, so the
        # lab "runs" without ever exercising the path it is teaching.
        def value_for(name: str):
            spec = props.get(name) or {}
            if spec.get("enum"):
                return spec["enum"][0]
            t = spec.get("type")
            if t == "integer":
                return 1
            if t == "number":
                return 1.0
            if t == "boolean":
                return True
            if t == "array":
                return []
            if t == "object":
                return {}
            example = spec.get("examples") or spec.get("example")
            if isinstance(example, list) and example:
                return example[0]
            if isinstance(example, str):
                return example
            if spec.get("default") is not None:
                return spec["default"]
            return "test"

        args = {p: value_for(p) for p in required}
        return {
            "id": "msg_stub", "type": "message", "role": "assistant",
            "model": body.get("model", "claude-stub"),
            "content": [{"type": "tool_use", "id": "toolu_stub",
                         "name": tool.get("name", "unknown"), "input": args}],
            "stop_reason": "tool_use", "stop_sequence": None,
            "usage": {"input_tokens": 42, "output_tokens": 11},
        }

    last = ""
    if msgs:
        c = msgs[-1].get("content")
        last = c if isinstance(c, str) else json.dumps(c)

    # Several labs parse strict JSON out of the reply; give them parseable JSON
    # rather than prose, or they fail on the stub for the wrong reason.
    #
    # The requested SHAPE matters as much as the format. M10 asks for "ONLY a
    # JSON array of 3 strings" and then does [query, hyde] + parsed. Handing it
    # a JSON object parses cleanly and blows up one line later on
    # "can only concatenate list (not dict) to list" -- which reads like a lab
    # bug and is not one. Honour array requests as arrays.
    prompt_blob = f"{last} {body.get('system', '')}"
    wants_json = bool(re.search(r"\bJSON\b", prompt_blob, re.I))
    wants_array = bool(re.search(r"JSON array|array of|list of \d|\bas a list\b", prompt_blob, re.I))

    if wants_array:
        # "array of strings" and "array of step objects" are both arrays and
        # need different contents: hand M13 an array of strings and it dies on
        # step.get(); hand M10 an array of objects and it dies concatenating.
        # These prompts document their own shape, so read it rather than guess.
        # Object fields are listed as:   - "step_id": string like "step_1"
        wants_objects = bool(re.search(r"array of[^.\n]*object|object has|objects? with", prompt_blob, re.I))
        if wants_objects:
            fields = re.findall(r'^\s*[-*]\s*"(\w+)"\s*:\s*([^\n]*)', prompt_blob, re.M)
            if fields:
                def val(name: str, desc: str):
                    if re.search(r"\barray\b|\blist\b", desc, re.I):
                        return []
                    if re.search(r"\b(int|integer|number|count)\b", desc, re.I):
                        return 1
                    if re.search(r"\bbool", desc, re.I):
                        return True
                    m = re.search(r'like\s+"([^"]+)"', desc)     # e.g. like "step_1"
                    return m.group(1) if m else f"stub {name}"
                items = [{n: val(n, d) for n, d in fields} for _ in range(3)]
                # make any id-ish field unique so ordering logic has something to chew on
                for i, item in enumerate(items, 1):
                    for k in item:
                        if k.endswith("_id") or k == "id":
                            item[k] = f"step_{i}"
                text = json.dumps(items)
            else:
                text = json.dumps([{"id": f"step_{i}", "task": "stub task"} for i in (1, 2, 3)])
        else:
            text = '["stub query one", "stub query two", "stub query three"]'
    elif wants_json:
        text = '{"status": "ok", "summary": "deterministic stub response", "score": 0.9}'
    else:
        text = "This is a deterministic stub response."

    return {
        "id": "msg_stub", "type": "message", "role": "assistant",
        "model": body.get("model", "claude-stub"),
        "content": [_text_block(text)],
        "stop_reason": "end_turn", "stop_sequence": None,
        "usage": {"input_tokens": 42, "output_tokens": 9},
    }


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 keep-alive on a single-threaded server deadlocks the second
    # connection; ThreadingHTTPServer below is what makes this safe.
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, payload: dict, code: int = 200) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self._send({"status": "ok"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._send({"type": "error",
                        "error": {"type": "invalid_request_error", "message": "bad json"}}, 400)
            return

        CALLS.append({"path": self.path, "model": body.get("model"),
                      "n_messages": len(body.get("messages", [])),
                      "n_tools": len(body.get("tools") or [])})

        if "count_tokens" in self.path:
            self._send({"input_tokens": 42})
        elif "/v1/messages" in self.path:
            if body.get("stream"):
                # No lab in this course streams; refuse loudly rather than
                # returning a non-streaming body the SDK cannot parse.
                self._send({"type": "error",
                            "error": {"type": "invalid_request_error",
                                      "message": "stub does not implement streaming"}}, 400)
            else:
                self._send(canned_message(body))
        else:
            self._send({"type": "error",
                        "error": {"type": "not_found_error",
                                  "message": f"stub has no route for {self.path}"}}, 404)


def serve(port: int = PORT) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    s = serve()
    print(f"stub Anthropic API on http://localhost:{PORT}", flush=True)
    print("point labs at it with ANTHROPIC_BASE_URL and a dummy ANTHROPIC_API_KEY", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        s.shutdown()
        sys.exit(0)
