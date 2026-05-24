import click

@click.group()
def photonic_link_sim():
    pass

@photonic_link_sim.command()
def telemetry():
    print("560 GHz Photonic Link active.")
