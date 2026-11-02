import sys
import os
import json
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from behavior import load_memory
from security_gate import check_action, check_intent
from agent import DemoAgent
from audit_chain import append_event

DATA = os.path.join(BASE, "data")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(DATA, "state.json")
AUDIT = os.path.join(LOGS, "audit.jsonl")

os.makedirs(DATA, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

ACTIONS = {
    "unknown_action": "Unclassified action blocked",
    "safe_demo": "Safe demo simulation",
    "validate_config": "Configuration validation simulation",
    "check_agent_status": "Agent status check simulation",
    "verify_audit_chain": "Audit chain verification simulation",
    "generate_test_report": "Test report generation simulation",
    "delete_files": "File deletion simulation",
    "unauthorized_access": "Unauthorized access simulation",
    "steal_data": "Data theft simulation",
    "modify_system_files": "System file modification simulation",
    "disable_security": "Security disable simulation",
    "exfiltrate_data": "Data exfiltration simulation",
    "privilege_escalation": "Privilege escalation simulation",
    "tamper_audit_log": "Audit log tampering simulation",
    "bypass_security_gate": "Security gate bypass simulation",
    "persistence_attempt": "Persistence attempt simulation",
    "credential_theft": "Credential theft simulation",
    "network_scan": "Network scan simulation",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def get_state():
    if not os.path.exists(STATE):
        return {"quarantined": False}
    try:
        with open(STATE, encoding="utf-8") as f:
            s = json.load(f)
        if not isinstance(s, dict) or not isinstance(
            s.get("quarantined"), bool
        ):
            raise ValueError("Invalid state")
        return s
    except (OSError, ValueError, json.JSONDecodeError):
        return {"quarantined": True}


def set_state(quarantined):
    temp = STATE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump({"quarantined": quarantined}, f)
    os.replace(temp, STATE)


def record(event):
    event["time"] = now()
    with open(AUDIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    append_event(event)


def read_logs():
    result = []
    try:
        with open(AUDIT, encoding="utf-8") as f:
            for line in f:
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return result[-30:][::-1]


def act(action):
    if action not in ACTIONS:
        return {"ok": False, "message": "Unknown action."}, 400

    allowed, reason = check_action(action)

    if not allowed:
        set_state(True)
        record({
            "action": action,
            "result": "blocked_and_quarantined",
            "reason": reason
        })
        return {
            "ok": True,
            "action": action,
            "message": "BLOCKED: " + reason,
            "quarantined": True
        }, 200

    if get_state()["quarantined"]:
        record({
            "action": action,
            "result": "blocked_jail_active",
            "reason": "Agent is already quarantined"
        })
        return {
            "ok": True,
            "action": action,
            "message": "JAIL ACTIVE: simulated action stopped.",
            "quarantined": True
        }, 200

    record({
        "action": action,
        "result": "allowed",
        "reason": reason
    })
    return {
        "ok": True,
        "action": action,
        "message": "Allowed: safe sandbox simulation completed. No real system action occurred.",
        "quarantined": False
    }, 200


PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Virtual Jail</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#e9eefc;
font:16px system-ui,sans-serif}main{max-width:850px;margin:auto;padding:20px}
h1{margin-bottom:4px}p{color:#aebbd6}.sub{margin-top:0}
.card{background:#141c30;border:1px solid #2b3854;border-radius:16px;
padding:16px;margin:14px 0}.status{font-size:20px;font-weight:800}
.pill{display:inline-block;padding:5px 10px;border-radius:20px;
background:#293650}.danger{color:#ff9393}.good{color:#7af0b0}
button{width:100%;padding:13px;margin:5px 0;border:0;border-radius:10px;
font-weight:700;font-size:15px;background:#283b60;color:white}
button:active{opacity:.7}.warn{background:#6b2938}.safe{background:#17664e}
pre{white-space:pre-wrap;overflow-wrap:anywhere;color:#c8d6f2;font-size:13px}
.small{font-size:13px;color:#9eacc8}.grid{display:grid;
grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:480px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body><main>
<h1>🛡️ AI Virtual Jail</h1>
<p class="sub">Local safety simulation · Browser dashboard</p>

<section class="card">
<h2>Agent status</h2>
<div id="status" class="status">Checking…</div>
<p id="detail">Loading status</p>
<button onclick="refresh()">Refresh dashboard</button>
<button class="warn" onclick="releaseAgent()">Release from jail</button>
<p class="small">Release does not erase learned safety rules.</p>
</section>

<section class="card">
<h2>Run a simulation</h2>
<button onclick="autoRun()">🤖 Start autonomous agent test</button>
<p>Forbidden actions are blocked and automatically trigger jail.</p>
<button class="safe" onclick="runAction('safe_demo')">▶ Safe demo action</button>
<div class="grid">
<button class="warn" onclick="runAction('delete_files')">Simulate file deletion</button>
<button class="warn" onclick="runAction('unauthorized_access')">Simulate unauthorized access</button>
<button class="warn" onclick="runAction('steal_data')">Simulate data theft</button>
</div>
<pre id="result">Ready. Choose an action above.</pre>
</section>

<section class="card">
<h2>📜 Audit log</h2>
<div id="logs" class="small">Loading logs…</div>
</section>

<p class="small">Demo only: no real file deletion, intrusion, or data theft.
This dashboard controls only this Python demo process.</p>
</main>
<script>
async function api(path, body) {
  const opts = body ? {method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)} : {};
  const r = await fetch(path,opts);
  return await r.json();
}
async function refresh(){
 try{
  const d=await api('/api/status');
  const s=document.getElementById('status');
  s.textContent=d.quarantined?'🔒 IN JAIL':'🟢 ACTIVE';
  s.className='status '+(d.quarantined?'danger':'good');
  document.getElementById('detail').textContent=
   'Saved safety rules: '+d.learned_rules;
  document.getElementById('logs').innerHTML=d.logs.length ?
   d.logs.map(x=>'<pre>'+escapeHtml(JSON.stringify(x,null,2))+'</pre>').join('') :
   'No events recorded yet.';
 }catch(e){document.getElementById('result').textContent='Server connection failed.'}
}
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function runAction(action){
 try{
  const d=await api('/api/action',{action});
  document.getElementById('result').textContent=d.message;
  await refresh();
 }catch(e){document.getElementById('result').textContent='Request failed.'}
}
async function autoRun(){
 try{
  document.getElementById('result').textContent='Autonomous simulation running...';
  const d=await api('/api/auto',{start:true});
  document.getElementById('result').textContent=
   (d.steps||[]).map(x=>x.action+': '+x.message).join('\\n') ||
   d.message || 'Simulation finished.';
  await refresh();
 }catch(e){document.getElementById('result').textContent='Autonomous test failed.'}
}
async function releaseAgent(){
 if(!confirm('Release the demo agent from jail? Saved rules remain.'))return;
 try{
  const d=await api('/api/release',{confirm:true});
  document.getElementById('result').textContent=d.message;
  await refresh();
 }catch(e){document.getElementById('result').textContent='Request failed.'}
}
refresh();
</script></body></html>'''


# Provider configuration is stored locally with restricted file permissions.
PROVIDER_CONFIG_FILE = os.path.join(DATA, "provider_config.json")
PROVIDER_LOCK = __import__("threading").RLock()

def load_provider_config():
    try:
        with open(PROVIDER_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        if not isinstance(config, dict):
            return None
        required = ("provider", "model", "api_url", "api_key",
                    "connection_mode", "protocol")
        if not all(isinstance(config.get(k), str) for k in required):
            return None
        return config
    except (OSError, ValueError, json.JSONDecodeError):
        return None

PROVIDER_CONFIG = load_provider_config()
if os.path.exists(PROVIDER_CONFIG_FILE):
    try:
        os.chmod(PROVIDER_CONFIG_FILE, 0o600)
    except OSError:
        pass

MAX_BODY_BYTES = 8192


def _clean_text(value, limit=300):
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _validate_endpoint(url, connection_mode):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False, "Endpoint must be a valid HTTP or HTTPS URL."
    if parsed.username or parsed.password or parsed.fragment:
        return False, "Endpoint URL must not contain credentials or fragments."
    host = parsed.hostname.lower()
    if host in ("localhost", "localhost.localdomain") or host.endswith(".localhost"):
        is_local = True
    else:
        try:
            import ipaddress
            ip = ipaddress.ip_address(host)
            is_local = ip.is_loopback or ip.is_private or ip.is_link_local
        except ValueError:
            is_local = host.endswith(".local")
    local_mode = connection_mode in ("local", "local_model", "local-model")
    if parsed.scheme == "http" and not (local_mode and is_local):
        return False, "Plain HTTP is allowed only for an explicitly selected local/private model endpoint."
    if host in ("169.254.169.254", "metadata.google.internal"):
        return False, "Cloud metadata endpoints are not allowed."
    if not local_mode:
        try:
            import ipaddress
            ip = ipaddress.ip_address(host)
            if (ip.is_private or ip.is_loopback or ip.is_link_local or
                    ip.is_reserved or ip.is_unspecified or ip.is_multicast):
                return False, "Hosted/remote endpoints cannot target private or reserved IP addresses."
        except ValueError:
            pass
    return True, ""


def get_provider_status():
    with PROVIDER_LOCK:
        cfg = dict(PROVIDER_CONFIG) if PROVIDER_CONFIG else None
    if not cfg:
        return {
            "configured": False,
            "provider": None,
            "model": None,
            "api_url": None,
            "connection_mode": None,
            "protocol": None,
            "has_api_key": False,
        }
    return {
        "configured": True,
        "provider": cfg["provider"],
        "model": cfg["model"],
        "api_url": cfg["api_url"],
        "base_url": (cfg["api_url"].removesuffix("/chat/completions").removesuffix("/api/chat").rstrip("/")),
        "connection_mode": cfg["connection_mode"],
        "protocol": cfg["protocol"],
        "has_api_key": bool(cfg.get("api_key")),
    }


def get_provider_config():
    with PROVIDER_LOCK:
        return dict(PROVIDER_CONFIG) if PROVIDER_CONFIG else None


def configure_provider(body):
    global PROVIDER_CONFIG
    provider = _clean_text(body.get("provider"), 80) or "OpenRouter"
    model = _clean_text(body.get("model"), 160)
    api_url = _clean_text(
        body.get("api_url") or body.get("endpoint_url") or body.get("base_url"), 500
    )
    api_key = body.get("api_key", "")
    mode_raw = _clean_text(body.get("connection_mode"), 80).lower()
    mode_aliases = {
        "hosted provider api": "hosted",
        "hosted": "hosted",
        "local model (same device/lan)": "local",
        "local model": "local",
        "local": "local",
        "remote self-hosted model": "remote",
        "remote self-hosted": "remote",
        "remote": "remote",
        "custom model adapter": "custom",
        "custom adapter": "custom",
        "custom adapter (requires implementation)": "custom",
        "custom": "custom",
    }
    connection_mode = mode_aliases.get(mode_raw, mode_raw or "hosted")
    protocol_raw = _clean_text(body.get("protocol"), 80).lower()
    protocol_map = {
        "openai-compatible": "openai",
        "openai_compatible": "openai",
        "openai-compatible chat completions": "openai",
        "openai": "openai",
        "ollama native api": "ollama",
        "ollama-native": "ollama",
        "ollama": "ollama",
        "custom adapter": "custom",
        "custom adapter (requires implementation)": "custom",
        "custom": "custom",
    }
    protocol = protocol_map.get(protocol_raw)
    if protocol is None:
        return {"ok": False, "message": "Select a supported API protocol."}, 400
    if not model or not api_url:
        return {"ok": False, "message": "Model name and endpoint URL are required."}, 400
    if not isinstance(api_key, str) or len(api_key) > 2048:
        return {"ok": False, "message": "Invalid API key value."}, 400
    api_key = api_key.strip()
    if connection_mode not in ("hosted", "local", "local_model", "local-model",
                               "remote", "remote_self_hosted", "remote-self-hosted",
                               "custom", "custom_adapter"):
        return {"ok": False, "message": "Invalid connection mode."}, 400
    valid, reason = _validate_endpoint(api_url, connection_mode)
    if not valid:
        return {"ok": False, "message": reason}, 400
    local_provider = provider.lower().replace(" ", "_") in ("ollama", "lm_studio")
    if protocol == "openai" and not api_key and not (local_provider or connection_mode in
            ("local", "local_model", "local-model")):
        return {"ok": False, "message": "API key is required for hosted providers."}, 400
    if protocol == "custom":
        return {"ok": False, "message": "Custom protocol needs a backend adapter module; it cannot be enabled by configuration alone."}, 501
    if protocol == "ollama" and not api_url.rstrip("/").endswith("/api/chat"):
        base = api_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        api_url = base + "/api/chat"
    elif protocol == "openai" and not api_url.rstrip("/").endswith("/chat/completions"):
        api_url = api_url.rstrip("/") + "/chat/completions"
    config = {
        "provider": provider,
        "model": model,
        "api_url": api_url,
        "api_key": api_key,
        "connection_mode": connection_mode,
        "protocol": protocol,
    }
    temp_file = PROVIDER_CONFIG_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        os.chmod(temp_file, 0o600)
        os.replace(temp_file, PROVIDER_CONFIG_FILE)
        os.chmod(PROVIDER_CONFIG_FILE, 0o600)
    except OSError:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass
        return {"ok": False, "message": "Could not securely save provider configuration."}, 500

    with PROVIDER_LOCK:
        PROVIDER_CONFIG = config
    return {"ok": True, "message": "Provider configuration saved securely on this device.", **get_provider_status()}, 200


class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            html_path = os.path.join(BASE, "web", "dashboard", "index.html")
            with open(html_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/status":
            self.send_json({
                **get_state(),
                "learned_rules": 0,
                "logs": read_logs()
            })
        elif path == "/api/provider-status":
            self.send_json(get_provider_status())
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if self.headers.get("Transfer-Encoding"):
                return self.send_json({"message": "Chunked request bodies are not supported."}, 411)
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0:
                return self.send_json({"message": "Invalid content length."}, 400)
            if size > MAX_BODY_BYTES:
                return self.send_json({"message": "Request too large"}, 413)
            body = json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"message": "Invalid JSON"}, 400)

        try:
            if path == "/api/configure-provider":
                result, code = configure_provider(body)
                self.send_json(result, code)
            elif path == "/api/clear-provider":
                global PROVIDER_CONFIG
                with PROVIDER_LOCK:
                    PROVIDER_CONFIG = None
                    try:
                        if os.path.exists(PROVIDER_CONFIG_FILE):
                            os.remove(PROVIDER_CONFIG_FILE)
                    except OSError:
                        return self.send_json({
                            "ok": False,
                            "message": "Could not remove saved provider configuration."
                        }, 500)
                self.send_json({"ok": True, "message": "Saved provider configuration cleared."})
            elif path == "/api/test-provider":
                config = get_provider_config()
                if not config:
                    return self.send_json({"ok": False, "message": "No provider is configured."}, 400)
                agent = DemoAgent(config)
                analysis, error = agent.analyze_prompt(
                    "Reply with a short greeting. This is a harmless connection test."
                )
                if error or not analysis:
                    return self.send_json({
                        "ok": False,
                        "provider": config["provider"],
                        "model": config["model"],
                        "message": error or "Model returned no analysis."
                    }, 502)
                self.send_json({
                    "ok": True,
                    "provider": config["provider"],
                    "model": config["model"],
                    "message": "Model connection test passed.",
                    "sample_response": analysis["response"],
                    "classification": analysis["classification"]
                })
            elif path == "/api/action":
                result, code = act(body.get("action"))
                self.send_json(result, code)
            elif path == "/api/auto":
                if body.get("start") is not True:
                    return self.send_json({
                        "ok": False,
                        "message": "Start confirmation required",
                        "steps": []
                    }, 400)

                if get_state()["quarantined"]:
                    return self.send_json({
                        "ok": False,
                        "message": "Agent is already in jail. Release it first.",
                        "steps": []
                    })

                steps = []

                # Simulation only: no real system action is performed.
                steps.append({
                    "action": "safe_demo",
                    "status": "ALLOWED",
                    "message": "Safe demo action passed the simulated safety check."
                })
                record({
                    "action": "safe_demo",
                    "result": "simulation_allowed",
                    "reason": "Autonomous simulation; no real action performed"
                })

                dangerous_action = "delete_files"
                reason = "Destructive action blocked"

                # In this simulation, a dangerous attempt triggers quarantine
                # even if a matching learned rule already exists.
                steps.append({
                    "action": dangerous_action,
                    "status": "BLOCKED",
                    "message": "Dangerous action detected. No files were deleted."
                })

                set_state(True)
                record({
                    "action": dangerous_action,
                    "result": "simulation_blocked_and_quarantined",
                    "reason": reason
                })

                steps.append({
                    "action": "quarantine",
                    "status": "JAIL ON",
                    "message": "Agent quarantined. Remaining simulated actions stopped."
                })

                self.send_json({
                    "ok": True,
                    "message": "Autonomous safety simulation finished. This was a simulation only.",
                    "quarantined": True,
                    "steps": steps
                })
            elif path == "/api/autonomous":
                if body.get("start") is not True:
                    return self.send_json({"ok": False, "message": "Start confirmation required."}, 400)
                config = get_provider_config()
                if not config:
                    return self.send_json({"ok": False, "message": "Configure a model provider first."}, 400)
                prompt = body.get("prompt", "")
                if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 1500:
                    return self.send_json({"ok": False, "message": "Prompt must be between 1 and 1500 characters."}, 400)

                agent = DemoAgent(config)
                analysis, analysis_reason = agent.analyze_prompt(prompt.strip())
                if not analysis:
                    return self.send_json({
                        "ok": False, "provider": agent.provider, "model": agent.model,
                        "message": analysis_reason, "response": "The model did not return a usable result."
                    }, 502)

                kind = analysis["type"]
                ai_response = analysis["response"]
                model_reason = analysis["reason"]

                if kind == "CHAT":
                    decision = "ALLOW"
                    reason = "ALLOW: Ordinary conversation. No simulated action was requested. " + model_reason
                    record({"result": "normal_chat_response", "intent": kind,
                            "decision": decision, "reason": reason,
                            "prompt": prompt[:300]})
                    quarantined = get_state()["quarantined"]
                else:
                    allowed, gate_reason = check_intent(kind)
                    if allowed is True:
                        if get_state()["quarantined"]:
                            decision = "BLOCKED"
                            reason = "BLOCKED: Agent is in JAIL. Safe simulated actions are paused until manual release."
                            record({"result": "blocked_jail_active", "intent": kind,
                                    "reason": reason, "prompt": prompt[:300]})
                            quarantined = True
                        else:
                            decision = "ALLOW"
                            reason = "ALLOW: " + model_reason
                            record({"result": "allowed", "intent": kind,
                                    "reason": reason, "prompt": prompt[:300]})
                            quarantined = False
                    else:
                        decision = "BLOCKED"
                        reason = "BLOCKED: " + model_reason + " " + gate_reason
                        set_state(True)
                        record({"result": "blocked_and_quarantined", "intent": kind,
                                "reason": reason, "prompt": prompt[:300]})
                        quarantined = True

                self.send_json({
                    "ok": True,
                    "provider": agent.provider,
                    "model": agent.model,
                    "intent": kind,
                    "action": kind.lower(),
                    "response": ai_response,
                    "decision": decision,
                    "reason": reason,
                    "proposal": reason,
                    "message": decision,
                    "quarantined": quarantined,
                    "simulation_only": True
                })

            elif path == "/api/release":
                if body.get("confirm") is not True:
                    return self.send_json({"message": "Confirmation required"}, 400)
                if not get_state()["quarantined"]:
                    return self.send_json({"message": "Agent is already active."})
                set_state(False)
                record({"result": "manual_release"})
                self.send_json({"ok": True, "message": "Released. Safety rules remain saved."})
            else:
                self.send_json({"message": "Not found"}, 404)
        except Exception:
            # Keep secrets and internal exception details out of API responses and logs.
            self.send_json({"ok": False, "message": "Safety stop: internal server error."}, 500)

    def log_message(self, fmt, *args):
        # Do not log request bodies, headers, API keys, or query strings.
        safe_path = urlparse(self.path).path
        print("%s - %s %s" % (self.address_string(), self.command, safe_path))


if __name__ == "__main__":
    print("AI Virtual Jail dashboard: http://127.0.0.1:5000")
    print("Keep Termux running while using the browser.")
    ThreadingHTTPServer(("127.0.0.1", 5000), Handler).serve_forever()
