from agent import DemoAgent
from security_gate import check_action


def main():
    agent = DemoAgent()

    print("Requesting one AI action proposal...")
    action, message = agent.propose_action()

    print("Status:", message)

    if action is None:
        print("No valid proposal; nothing was executed.")
        return

    print("Proposed action:", action)

    allowed, reason = check_action(action)
    print("Security gate:", "ALLOW" if allowed else "BLOCK")
    print("Reason:", reason)
    print("Simulation only: no action was executed.")


if __name__ == "__main__":
    main()
