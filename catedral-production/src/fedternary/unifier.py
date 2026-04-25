class FedTernaryUnifier:
    def aggregate(self, gradients):
        if not gradients: return 0
        return sum(gradients) / len(gradients)
