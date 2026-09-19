"""Country-aware expert sharding."""
BRICS_COUNTRIES = ("BR", "RU", "IN", "CN", "ZA")
def shard_by_country(experts, max_share_per_country: float = 0.50):
    if not 0 < max_share_per_country <= 1: raise ValueError("max_share_per_country must be in (0, 1]")
    if experts and 1 / len(BRICS_COUNTRIES) > max_share_per_country: raise ValueError("share cap cannot support the configured countries")
    for index, expert in enumerate(experts): expert["country"] = BRICS_COUNTRIES[index % len(BRICS_COUNTRIES)]
    return experts
