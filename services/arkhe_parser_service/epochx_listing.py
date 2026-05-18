# epochx_listing.py
from substrate_210.epochx_marketplace import EpochXMarketplace
from substrate_141.x402 import x402

marketplace = EpochXMarketplace(endpoint="https://epochx.arkhe.org")

# Descreve o serviço de parsing
service = marketplace.register_service(
    name="Arkhe Universal Parser",
    description="Parse any code (COBOL, Python, Rust, etc.) into canonical AST, check security, generate Arkhe Tokens",
    price_per_call=0.01,  # USDC via x402
    price_model="per_parse",
    energy_adjustment=True,  # usa Energy Oracle para modificar preço em tempo real
    endpoint="https://parser.arkhe.org/parse"
)

print(f"Service registered with ID {service.id}")