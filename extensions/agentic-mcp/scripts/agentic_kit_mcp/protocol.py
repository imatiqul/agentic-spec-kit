"""The part of the Model Context Protocol that the server needs, written by hand (MCP-4 to MCP-7).

JSON-RPC 2.0, one message a line. Two ways of opening are served, request by request:

* the handshake of revisions 2024-11-05 to 2025-11-25: `initialize`, `notifications/initialized`, `ping`,
  `tools/list`, `tools/call`;
* revision 2026-07-28, which has no handshake: a request carries its protocol version and the client's
  capabilities in `params._meta`, and `server/discover` says what the server is.

The specification was read on modelcontextprotocol.io on 2026-11-26; `docs/design/mcp-server.md` lists the pages
and what follows from them. Nothing here knows the kit or what a tool does: a tool is a name, a description, a
schema and a function that takes its arguments and returns text. Nothing here reads or writes a stream either:
the caller hands in each line and a function that sends one.
"""
from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Iterable

#: Revisions in which every request says which revision it speaks. Newest first.
MODERN = ("2026-07-28",)
#: Revisions that open with `initialize`. Newest first: the first is what an unknown revision is answered with.
HANDSHAKE = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
BATCHES = "2025-03-26"         # the one revision in which a line may hold a JSON array of messages
NO_ANNOTATIONS = "2024-11-05"  # tool annotations came with 2025-03-26

VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"
SUBSCRIPTION_KEY = "io.modelcontextprotocol/subscriptionId"

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = -32700, -32600, -32601, -32602, -32603
UNSUPPORTED_VERSION = -32022   # defined by revision 2026-07-28

#: The server offers tools, and never says that their list changed: it is fixed while the server runs.
CAPABILITIES = {"tools": {"listChanged": False}}
#: 2026-07-28 asks for both on `server/discover` and `tools/list`. No promise of time: a new server after an update of
#: the kit may list other tools. Public: the list says nothing about a person.
CACHE = {"ttlMs": 0, "cacheScope": "public"}
NOT_OPENED = ("Invalid params: the request names no protocol version. Send `initialize` first, or put "
              f"`{VERSION_KEY}` and `{CAPABILITIES_KEY}` in `params._meta`")
#: The words of JSON Schema that `check_arguments` reads. A tool whose schema uses another is refused when the server starts.
SCHEMA_WORDS = {"type", "properties", "required", "additionalProperties", "description", "enum", "minLength", "maxLength",
                "minimum", "maximum", "default", "items", "maxItems"}


class Refused(Exception):
    """A tool's "no": it was given something it will not take, or the kit could not answer. Its words go to the model."""


class Gone(Exception):
    """The client no longer reads what the server sends. The caller's `send` raises it, and the server stops."""


class RpcError(Exception):
    """An answer that is a JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data


@dataclass(frozen=True)
class Tool:
    name: str
    title: str
    description: str
    schema: dict
    run: Callable[[dict], str]  # the arguments, already checked against the schema -> the text of the result
    open_world: bool = False    # does it reach anything beyond the project's own files?
    writes: bool = False        # does it change a file? Only where the server was started with --allow-write (MCW-1)
    idempotent: bool = False    # for a tool that writes: does a second call with the same arguments change nothing more?


def _schema_words(schema: Any) -> set:
    found: set = set()
    if isinstance(schema, dict):
        found |= set(schema)
        for rule in (schema.get("properties") or {}).values():
            found |= _schema_words(rule)
        found |= _schema_words(schema.get("items"))
    return found


def _wrong(rule: dict, value: Any) -> str | None:
    """What is wrong with one argument, as the end of a sentence that starts with its name; None when nothing is."""
    kind = rule.get("type")
    if kind == "string":
        if not isinstance(value, str):
            return "must be text"
        if "enum" in rule and value not in rule["enum"]:
            return "must be one of " + ", ".join(rule["enum"])
        if len(value) < rule.get("minLength", 0):
            return "must not be empty" if rule["minLength"] == 1 else f"must have at least {rule['minLength']} characters"
        if "maxLength" in rule and len(value) > rule["maxLength"]:
            return f"must have at most {rule['maxLength']} characters"
    elif kind == "integer":
        if isinstance(value, bool) or not (isinstance(value, int) or (isinstance(value, float) and value.is_integer())):
            return "must be a whole number"
        low, high = rule.get("minimum"), rule.get("maximum")
        if (low is not None and value < low) or (high is not None and value > high):
            return f"must be from {low} to {high}" if low is not None and high is not None else \
                (f"must be at least {low}" if low is not None else f"must be at most {high}")
    elif kind == "boolean":
        if not isinstance(value, bool):
            return "must be true or false"
    elif kind == "array":
        if not isinstance(value, list):
            return "must be a list"
        if "maxItems" in rule and len(value) > rule["maxItems"]:
            return f"must have at most {rule['maxItems']} entries"
        for entry in value:
            wrong = _wrong(rule.get("items") or {}, entry)
            if wrong:
                return f"is a list in which each entry {wrong}"
    return None


def check_arguments(schema: dict, arguments: dict) -> list[str]:
    """What is wrong with a tool's arguments, in words a model can act on. An empty list when nothing is (MCP-18).

    This reads the few words of JSON Schema that the tools' own schemas use (`SCHEMA_WORDS`). It is not a JSON Schema
    validator, and it does not need to be one: the schemas are the server's own."""
    problems = []
    properties = schema.get("properties") or {}
    for name in schema.get("required") or []:
        if name not in arguments:
            problems.append(f"`{name}` is required")
    for name, value in arguments.items():
        if name not in properties:
            takes = ", ".join(f"`{known}`" for known in properties) or "no argument"
            problems.append(f"`{str(name)[:40]}` is not an argument of this tool, which takes {takes}")
            continue
        wrong = _wrong(properties[name], value)
        if wrong:
            problems.append(f"`{name}` {wrong}")
    return problems


def _is_id(value: Any) -> bool:
    """A request id as MCP has it: text or a whole number, and never null."""
    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _error(rid: Any, code: int, message: str, data: Any = None) -> dict:
    """An error answer. `rid` is None where no id could be read: JSON-RPC 2.0 then asks for `"id": null`."""
    body: dict = {"code": code, "message": message}
    if data is not None:
        body["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": body}


class Server:
    """Answers one line at a time. It keeps two things between lines: the revision a handshake agreed on, and the
    ids of `subscriptions/listen` requests that are still open. A request of revision 2026-07-28 uses neither."""

    def __init__(self, tools: Iterable[Tool], name: str, version: str, instructions: str, send: Callable[[bytes], None],
                 finish: Callable[[str], str] = lambda text: text, log: Callable[[str], None] = lambda line: None):
        self.tools = list(tools)
        for tool in self.tools:
            unknown = _schema_words(tool.schema) - SCHEMA_WORDS
            if unknown or tool.schema.get("type") != "object" or tool.schema.get("additionalProperties") is not False:
                raise ValueError(f"the schema of {tool.name} is not one this server can check: {sorted(unknown) or 'its root'}")
        self.by_name = {tool.name: tool for tool in self.tools}
        self.info = {"name": name, "version": version}
        self.instructions = instructions
        self._out, self.finish, self.log = send, finish, log
        self.handshake: str | None = None  # the revision `initialize` agreed on, for the rest of the process
        self.listening: list = []          # ids of open `subscriptions/listen` requests

    # ── lines in, lines out ─────────────────────────────────────────────────────────

    def serve(self, lines: Iterable[bytes]) -> None:
        """Every line until the client closes its end; then each open subscription is ended with its result."""
        for raw in lines:
            self.receive(raw)
        self.close()

    def receive(self, raw: bytes) -> None:
        """One line from the client. Whatever it holds, the answer is what JSON-RPC asks for, and the server goes on."""
        if not raw.strip():
            return
        try:
            message = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            self._send(_error(None, PARSE_ERROR, "Parse error: the line is not JSON in UTF-8"))
            return
        if isinstance(message, list):
            self._batch(message)
            return
        reply = self._one(message)
        if reply is not None:
            self._send(reply)

    def close(self) -> None:
        for rid in self.listening:
            self._send({"jsonrpc": "2.0", "id": rid, "result": {"resultType": "complete", "_meta": {SUBSCRIPTION_KEY: rid, SERVER_INFO_KEY: self.info}}})
        self.listening = []

    def _send(self, message: Any) -> None:
        # ASCII only, so no byte of a message can be read as a line break, whatever the text of a file holds.
        self._out(json.dumps(message, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n")

    def _batch(self, messages: list) -> None:
        if self.handshake != BATCHES:
            self._send(_error(None, INVALID_REQUEST, f"Invalid Request: a line holds one message. A batch is part of revision {BATCHES} only"))
            return
        if not messages:
            self._send(_error(None, INVALID_REQUEST, "Invalid Request: an empty batch"))
            return
        replies = []
        for message in messages:
            if isinstance(message, dict) and message.get("method") == "initialize" and "id" in message:
                rid = message["id"] if _is_id(message["id"]) else None
                replies.append(_error(rid, INVALID_REQUEST, "Invalid Request: `initialize` is not sent in a batch"))
                continue
            reply = self._one(message)
            if reply is not None:
                replies.append(reply)
        if replies:  # a batch of notifications alone gets no answer
            self._send(replies)

    def _one(self, message: Any) -> dict | None:
        """The answer to one message, or None where there is none to give."""
        if not isinstance(message, dict):
            return _error(None, INVALID_REQUEST, "Invalid Request: a message is a JSON object")
        method = message.get("method")
        if not isinstance(method, str):
            if "result" in message or "error" in message:  # an answer: the server asks nothing, so it expects none
                self.log("ignored a response from the client: this server sends no request")
                return None
            return _error(message["id"] if _is_id(message.get("id")) else None, INVALID_REQUEST, "Invalid Request: `method` is missing")
        params = message.get("params")
        if "id" not in message:  # a notification: never answered, whatever it is
            self._notified(method, params)
            return None
        rid = message["id"]
        if not _is_id(rid):
            return _error(None, INVALID_REQUEST, "Invalid Request: `id` is text or a whole number")
        if message.get("jsonrpc") != "2.0":
            return _error(rid, INVALID_REQUEST, 'Invalid Request: `jsonrpc` must be "2.0"')
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return _error(rid, INVALID_PARAMS, "Invalid params: `params` is an object")
        try:
            result = self._request(rid, method, params)
        except RpcError as wrong:
            return _error(rid, wrong.code, wrong.message, wrong.data)
        except Gone:
            raise
        except Exception:  # noqa: BLE001 - the server's own failure: the client gets the code, the log gets the rest
            self.log(traceback.format_exc())
            return _error(rid, INTERNAL_ERROR, "Internal error")
        if result is None:  # `subscriptions/listen`: its result comes when the subscription ends
            return None
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def _notified(self, method: str, params: Any) -> None:
        if method == "notifications/cancelled" and isinstance(params, dict):
            wanted = params.get("requestId")
            # The client ends a subscription this way. A cancelled request gets no answer, so none follows.
            self.listening = [rid for rid in self.listening if not (type(rid) is type(wanted) and rid == wanted)]

    # ── which way the request came ──────────────────────────────────────────────────

    def _request(self, rid: Any, method: str, params: dict) -> dict | None:
        meta = params.get("_meta")
        if method == "initialize":  # the handshake. 2026-07-28 has none, so `_meta` does not change what this is
            return self._initialize(params)
        if isinstance(meta, dict) and VERSION_KEY in meta:
            return self._modern(rid, method, params, meta)
        return self._older(method, params)

    def _initialize(self, params: dict) -> dict:
        asked = params.get("protocolVersion")
        if not isinstance(asked, str):
            raise RpcError(INVALID_PARAMS, "Invalid params: `protocolVersion` is missing")
        self.handshake = asked if asked in HANDSHAKE else HANDSHAKE[0]
        return {"protocolVersion": self.handshake, "capabilities": CAPABILITIES, "serverInfo": self.info, "instructions": self.instructions}

    def _older(self, method: str, params: dict) -> dict:
        """A request that names no revision: served as the handshake's revision has it."""
        if method == "ping":
            return {}
        if method in ("server/discover", "subscriptions/listen"):  # these exist in 2026-07-28 only
            raise RpcError(INVALID_PARAMS, f"Invalid params: `{method}` needs `{VERSION_KEY}` and `{CAPABILITIES_KEY}` in `params._meta`")
        if method not in ("tools/list", "tools/call"):
            raise RpcError(METHOD_NOT_FOUND, "Method not found", method[:80])
        if self.handshake is None:
            raise RpcError(INVALID_PARAMS, NOT_OPENED)
        if method == "tools/list":
            return {"tools": self._listed(params, self.handshake)}
        return self._called(params)

    def _modern(self, rid: Any, method: str, params: dict, meta: dict) -> dict | None:
        """A request that says which revision it speaks: served on its own, with nothing remembered (2026-07-28)."""
        if CAPABILITIES_KEY not in meta:
            raise RpcError(INVALID_PARAMS, f"Invalid params: `params._meta` lacks `{CAPABILITIES_KEY}`")
        asked = meta[VERSION_KEY]
        if not isinstance(asked, str):
            raise RpcError(INVALID_PARAMS, f"Invalid params: `{VERSION_KEY}` is text")
        if asked not in MODERN:
            raise RpcError(UNSUPPORTED_VERSION, "Unsupported protocol version", {"supported": [*MODERN, *HANDSHAKE], "requested": asked[:80]})
        if method == "server/discover":
            result = {"supportedVersions": list(MODERN), "capabilities": CAPABILITIES, "instructions": self.instructions, **CACHE}
        elif method == "tools/list":
            result = {"tools": self._listed(params, asked), **CACHE}
        elif method == "tools/call":
            result = self._called(params)
        elif method == "subscriptions/listen":
            return self._listen(rid, params)
        else:  # `ping` too: 2026-07-28 took it out
            raise RpcError(METHOD_NOT_FOUND, "Method not found", method[:80])
        return {"resultType": "complete", **result, "_meta": {SERVER_INFO_KEY: self.info}}

    def _listen(self, rid: Any, params: dict) -> None:
        """Acknowledge a subscription and leave it open. The server has no notification to send, so it agrees to none."""
        if not isinstance(params.get("notifications", {}), dict):
            raise RpcError(INVALID_PARAMS, "Invalid params: `notifications` is an object")
        if not any(type(rid) is type(known) and rid == known for known in self.listening):
            self.listening.append(rid)
        self._send({"jsonrpc": "2.0", "method": "notifications/subscriptions/acknowledged",
                    "params": {"_meta": {SUBSCRIPTION_KEY: rid}, "notifications": {}}})

    # ── tools ───────────────────────────────────────────────────────────────────────

    def _listed(self, params: dict, version: str) -> list[dict]:
        if params.get("cursor") is not None:
            raise RpcError(INVALID_PARAMS, "Invalid params: this server gives out no cursor. Ask for the list without one")
        listed = []
        for tool in self.tools:
            entry = {"name": tool.name, "description": tool.description, "inputSchema": tool.schema}
            if version != NO_ANNOTATIONS:
                entry["annotations"] = {"title": tool.title, "readOnlyHint": not tool.writes, "openWorldHint": tool.open_world}
                if tool.writes:  # a tool of this server that writes only adds; the hint's default would say it may destroy (MCW-6)
                    entry["annotations"].update({"destructiveHint": False, "idempotentHint": tool.idempotent})
            listed.append(entry)
        return listed

    def _called(self, params: dict) -> dict:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise RpcError(INVALID_PARAMS, "Invalid params: `name`, the tool to call, is missing")
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise RpcError(INVALID_PARAMS, "Invalid params: `arguments` is an object")
        tool = self.by_name.get(name)
        if tool is None:
            raise RpcError(INVALID_PARAMS, f"Unknown tool: {name[:80]}")
        # From here on a "no" is a result the model can read and act on, not a protocol error (MCP-18).
        problems = check_arguments(tool.schema, arguments)
        if problems:
            text, failed = f"{name} was not called: " + "; ".join(problems) + ".", True
        else:
            try:
                text, failed = tool.run(dict(arguments)), False
            except Refused as no:
                text, failed = str(no), True
            except Gone:
                raise
            except Exception as wrong:  # noqa: BLE001 - whatever the kit raised: the model is told that it failed, the log gets the trace
                self.log(traceback.format_exc())
                said = " ".join(str(wrong).split())[:300]
                text, failed = f"{name} failed: {type(wrong).__name__}" + (f": {said}" if said else ""), True
        return {"content": [{"type": "text", "text": self.finish(text)}], "isError": failed}
