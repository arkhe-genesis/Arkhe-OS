#!/ Decreto: ORCID 0009‑0005‑2697‑4668
import click

CURRICULUM = {
    "P1": ["LLM Basics"]
}

@click.group()
def learn():
    """Navigate the ARKHE AI Foundations curriculum."""
    pass

@learn.command("list")
@click.option("--pillar", "-p", help="Filter by pillar (e.g., P1)")
def list_topics(pillar):
    """List all topics, optionally filtered by pillar."""
    for p_name, topics in CURRICULUM.items():
        if pillar and p_name != pillar:
            continue
        click.echo("\
{}:".format(p_name))
        for t in topics:
            click.echo("  • {}".format(t))

def register(cli):
    cli.add_command(learn)
