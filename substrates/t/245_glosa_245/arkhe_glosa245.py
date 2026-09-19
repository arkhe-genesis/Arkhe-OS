#!/usr/bin/env python3
import click

@click.group()
def cli():
    pass

@cli.command()
@click.option("--sequence", required=True, help="Sequência binária B(2,5)")
@click.option("--rpc", required=True, help="URL do nó Ethereum")
@click.option("--private-key", required=True, help="Chave privada do Arquiteto")
@click.option("--contract", required=True, help="Endereço do Glosa245Anchor")
def anchor(sequence, rpc, private_key, contract):
    """Ancora a sequência canônica no contrato Glosa245Anchor."""
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    expected_hash = Web3.keccak(text=sequence)
    # Construir transação
    contract_abi = [...]  # ABI do contrato
    anchor_contract = w3.eth.contract(address=contract, abi=contract_abi)
    tx = anchor_contract.functions.anchorSequence(sequence, expected_hash).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    click.echo(f"Transação enviada: {tx_hash.hex()}")

@cli.command()
@click.option("--hash", required=True, help="Hash da sequência")
@click.option("--rpc", required=True, help="URL do nó Ethereum")
@click.option("--contract", required=True, help="Endereço do Glosa245Anchor")
def verify(hash, rpc, contract):
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    contract_abi = [...]  # ABI do contrato
    anchor_contract = w3.eth.contract(address=contract, abi=contract_abi)
    # This is a stub for the real call, since we don't have a real ABI or connection
    # result = anchor_contract.functions.verifyHash(hash).call()
    result = True
    if result:
        click.echo("true")
    else:
        click.echo("false")

if __name__ == "__main__":
    cli()
