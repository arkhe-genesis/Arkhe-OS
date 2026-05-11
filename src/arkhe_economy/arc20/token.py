import hashlib
import time

class LambdaBackedToken:
    """
    Implementation of ARC-20: Token backed by coherence λ₂.
    """
    def __init__(self, name, symbol, min_lambda=0.85):
        self.name = name
        self.symbol = symbol
        self.min_lambda = min_lambda
        self.total_supply = 0
        self.balances = {}
        self.lambda_history = []

    def update_coherence(self, current_lambda):
        self.lambda_history.append((time.time(), current_lambda))
        # Keep 24h history
        if len(self.lambda_history) > 2880:
            self.lambda_history.pop(0)

    def calculate_mint_allowance(self):
        if not self.lambda_history:
            return 0

        current_lambda = self.lambda_history[-1][1]
        if current_lambda < self.min_lambda:
            return 0

        # Cumulative coherence integral (simplified)
        integral = sum(l[1]**2 for l in self.lambda_history) / len(self.lambda_history)
        return int(1000 * (1 + 0.1 * integral))

    def mint(self, agent_address, amount):
        if agent_address not in self.balances:
            self.balances[agent_address] = 0
        self.balances[agent_address] += amount
        self.total_supply += amount
        return True

    def slash_if_incoherent(self, agent_address):
        if not self.lambda_history:
            return 0

        current_lambda = self.lambda_history[-1][1]
        if current_lambda < 0.70:
            # Persistent decoherence: slash 50%
            slashed = self.balances.get(agent_address, 0) // 2
            self.balances[agent_address] -= slashed
            self.total_supply -= slashed
            return slashed
        return 0

if __name__ == "__main__":
    token = LambdaBackedToken("Rio-Coin", "RCO")
    token.update_coherence(0.99)
    allowance = token.calculate_mint_allowance()
    print(f"Mint Allowance: {allowance} {token.symbol}")
    token.mint("agent_01", allowance)
    print(f"Agent Balance: {token.balances['agent_01']}")

    token.update_coherence(0.65)
    slashed = token.slash_if_incoherent("agent_01")
    print(f"Slashed: {slashed} {token.symbol}")
    print(f"New Balance: {token.balances['agent_01']}")
