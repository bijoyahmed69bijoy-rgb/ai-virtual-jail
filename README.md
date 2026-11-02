🛡️ AI Virtual Jail

AI Virtual Jail is an experimental Python project for demonstrating AI-agent safety checks, simulated action blocking, quarantine behavior, and tamper-evident audit logging.

It includes a command-line interface and a local browser dashboard.

«Important: This is an educational simulation, not a production security system. It does not perform real file deletion, intrusion, or data theft.»

Features

- Simulated AI-agent safety checks
- Allowlist and deny-by-default action gate
- Quarantine simulation for blocked actions
- SHA-256 hash-chained audit records
- Local browser dashboard
- Optional AI-provider connection
- Automated unit and integration tests

Project Structure

ai-virtual-jail/
├── agent.py
├── audit_chain.py
├── behavior.py
├── main.py
├── security_gate.py
├── test_attacker_ai.py
├── tests/
├── data/
│   └── .gitkeep
├── web/
│   ├── server.py
│   └── dashboard/
│       └── index.html
├── .gitignore
└── README.md

Requirements

- Python 3.10 or newer recommended
- No third-party Python packages are required by the core modules inspected so far.

Installation

Clone the repository:
```
git clone https://github.com/bijoyahmed69bijoy-rgb/ai-virtual-jail.git
cd ai-virtual-jail
``` 

Run the CLI
```
python main.py
```

Run the Browser Dashboard

Start the local dashboard server:
```
python web/server.py
```
Open this address in your browser:
```
http://127.0.0.1:5000
```
Keep Termux running while using the dashboard.

Press "CTRL + C" in Termux to stop the server.

Run Tests
```
python -m unittest discover -s tests -v
```
Audit Logging

The project uses SHA-256 hash chaining to make changes to the recorded audit chain detectable during verification.

This is tamper-evident, not tamper-proof. It does not protect against an attacker who can rewrite the entire chain and its trusted reference.

AI Provider Configuration

The dashboard includes optional AI-provider configuration.

Provider credentials are stored locally. Never commit API keys, provider configuration files, or other secrets to GitHub.

Limitations

- Experimental educational project.
- Not a production security boundary.
- Simulated actions do not perform real system operations.
- AI classifications can be incorrect.
- Audit-chain verification cannot guarantee protection against every form of tampering.

License

No license has been selected yet. Unless a license is added, others do not automatically receive permission to reuse, modify, or redistribute this project.
