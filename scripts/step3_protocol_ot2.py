"""
Arkhe(n) Etapa 3 — Opentrons OT-2 + LED 405nm
Arkhe-Chain: 847.688 | Sigma-Level 2
"""

from opentrons import protocol_api

metadata = {
    'apiLevel': '2.13',
    'protocolName': 'Arkhe-Step3-Dispense-Polymerize',
    'author': 'Synapse-kappa',
    'created': '2026-04-06T19:33:27.666007+00:00',
}

def run(protocol: protocol_api.ProtocolContext):

    # Labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    led_module = protocol.load_module('magdeck', '4')  # LED array on magdeck

    # Pipettes
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack])

    # Parameters
    dispense_speed = 5000  # uL/min
    mix_reps = 3
    cooling_wait = 90.0

    # A1: Ciatico_Rato | 31.4 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(31.4, reservoir['A1'])
    p300.dispense(31.4, plate['A1'])
    p300.aspirate(50, plate['A1'])
    p300.dispense(50, plate['A1'])
    p300.aspirate(50, plate['A1'])
    p300.dispense(50, plate['A1'])
    p300.aspirate(50, plate['A1'])
    p300.dispense(50, plate['A1'])
    p300.blow_out(plate['A1'])
    p300.drop_tip()
    # Photopolymerize A1: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A2: Ciatico_Rato | 31.4 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(31.4, reservoir['A1'])
    p300.dispense(31.4, plate['A2'])
    p300.aspirate(50, plate['A2'])
    p300.dispense(50, plate['A2'])
    p300.aspirate(50, plate['A2'])
    p300.dispense(50, plate['A2'])
    p300.aspirate(50, plate['A2'])
    p300.dispense(50, plate['A2'])
    p300.blow_out(plate['A2'])
    p300.drop_tip()
    # Photopolymerize A2: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A3: Ciatico_Rato | 31.4 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(31.4, reservoir['A1'])
    p300.dispense(31.4, plate['A3'])
    p300.aspirate(50, plate['A3'])
    p300.dispense(50, plate['A3'])
    p300.aspirate(50, plate['A3'])
    p300.dispense(50, plate['A3'])
    p300.aspirate(50, plate['A3'])
    p300.dispense(50, plate['A3'])
    p300.blow_out(plate['A3'])
    p300.drop_tip()
    # Photopolymerize A3: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # C4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C4'])
    p300.blow_out(plate['C4'])
    p300.drop_tip()

    # C5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C5'])
    p300.blow_out(plate['C5'])
    p300.drop_tip()

    # C6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C6'])
    p300.blow_out(plate['C6'])
    p300.drop_tip()

    # C7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C7'])
    p300.blow_out(plate['C7'])
    p300.drop_tip()

    # C8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C8'])
    p300.blow_out(plate['C8'])
    p300.drop_tip()

    # C1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C1'])
    p300.blow_out(plate['C1'])
    p300.drop_tip()

    # C2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C2'])
    p300.blow_out(plate['C2'])
    p300.drop_tip()

    # C3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C3'])
    p300.blow_out(plate['C3'])
    p300.drop_tip()

    # E5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E5'])
    p300.blow_out(plate['E5'])
    p300.drop_tip()

    # E4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E4'])
    p300.blow_out(plate['E4'])
    p300.drop_tip()

    # E3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E3'])
    p300.blow_out(plate['E3'])
    p300.drop_tip()

    # E2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E2'])
    p300.blow_out(plate['E2'])
    p300.drop_tip()

    # E1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E1'])
    p300.blow_out(plate['E1'])
    p300.drop_tip()

    # D12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D12'])
    p300.blow_out(plate['D12'])
    p300.drop_tip()

    # D11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D11'])
    p300.blow_out(plate['D11'])
    p300.drop_tip()

    # D10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D10'])
    p300.blow_out(plate['D10'])
    p300.drop_tip()

    # D9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D9'])
    p300.blow_out(plate['D9'])
    p300.drop_tip()

    # D8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D8'])
    p300.blow_out(plate['D8'])
    p300.drop_tip()

    # D7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D7'])
    p300.blow_out(plate['D7'])
    p300.drop_tip()

    # D6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D6'])
    p300.blow_out(plate['D6'])
    p300.drop_tip()

    # D5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D5'])
    p300.blow_out(plate['D5'])
    p300.drop_tip()

    # D4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D4'])
    p300.blow_out(plate['D4'])
    p300.drop_tip()

    # D3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D3'])
    p300.blow_out(plate['D3'])
    p300.drop_tip()

    # D2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D2'])
    p300.blow_out(plate['D2'])
    p300.drop_tip()

    # D1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['D1'])
    p300.blow_out(plate['D1'])
    p300.drop_tip()

    # C12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C12'])
    p300.blow_out(plate['C12'])
    p300.drop_tip()

    # C11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C11'])
    p300.blow_out(plate['C11'])
    p300.drop_tip()

    # C10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C10'])
    p300.blow_out(plate['C10'])
    p300.drop_tip()

    # C9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['C9'])
    p300.blow_out(plate['C9'])
    p300.drop_tip()

    # E9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E9'])
    p300.blow_out(plate['E9'])
    p300.drop_tip()

    # E10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E10'])
    p300.blow_out(plate['E10'])
    p300.drop_tip()

    # E11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E11'])
    p300.blow_out(plate['E11'])
    p300.drop_tip()

    # E12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E12'])
    p300.blow_out(plate['E12'])
    p300.drop_tip()

    # F1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F1'])
    p300.blow_out(plate['F1'])
    p300.drop_tip()

    # E6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E6'])
    p300.blow_out(plate['E6'])
    p300.drop_tip()

    # E7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E7'])
    p300.blow_out(plate['E7'])
    p300.drop_tip()

    # E8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['E8'])
    p300.blow_out(plate['E8'])
    p300.drop_tip()

    # F3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F3'])
    p300.blow_out(plate['F3'])
    p300.drop_tip()

    # F2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F2'])
    p300.blow_out(plate['F2'])
    p300.drop_tip()

    # F4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F4'])
    p300.blow_out(plate['F4'])
    p300.drop_tip()

    # H1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H1'])
    p300.blow_out(plate['H1'])
    p300.drop_tip()

    # G12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G12'])
    p300.blow_out(plate['G12'])
    p300.drop_tip()

    # G11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G11'])
    p300.blow_out(plate['G11'])
    p300.drop_tip()

    # G10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G10'])
    p300.blow_out(plate['G10'])
    p300.drop_tip()

    # G9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G9'])
    p300.blow_out(plate['G9'])
    p300.drop_tip()

    # G8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G8'])
    p300.blow_out(plate['G8'])
    p300.drop_tip()

    # G7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G7'])
    p300.blow_out(plate['G7'])
    p300.drop_tip()

    # G6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G6'])
    p300.blow_out(plate['G6'])
    p300.drop_tip()

    # G5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G5'])
    p300.blow_out(plate['G5'])
    p300.drop_tip()

    # G4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G4'])
    p300.blow_out(plate['G4'])
    p300.drop_tip()

    # G3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G3'])
    p300.blow_out(plate['G3'])
    p300.drop_tip()

    # G2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G2'])
    p300.blow_out(plate['G2'])
    p300.drop_tip()

    # G1: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['G1'])
    p300.blow_out(plate['G1'])
    p300.drop_tip()

    # F12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F12'])
    p300.blow_out(plate['F12'])
    p300.drop_tip()

    # F11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F11'])
    p300.blow_out(plate['F11'])
    p300.drop_tip()

    # F10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F10'])
    p300.blow_out(plate['F10'])
    p300.drop_tip()

    # F9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F9'])
    p300.blow_out(plate['F9'])
    p300.drop_tip()

    # F8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F8'])
    p300.blow_out(plate['F8'])
    p300.drop_tip()

    # F7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F7'])
    p300.blow_out(plate['F7'])
    p300.drop_tip()

    # F6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F6'])
    p300.blow_out(plate['F6'])
    p300.drop_tip()

    # F5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['F5'])
    p300.blow_out(plate['F5'])
    p300.drop_tip()

    # H5: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H5'])
    p300.blow_out(plate['H5'])
    p300.drop_tip()

    # H6: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H6'])
    p300.blow_out(plate['H6'])
    p300.drop_tip()

    # H7: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H7'])
    p300.blow_out(plate['H7'])
    p300.drop_tip()

    # H8: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H8'])
    p300.blow_out(plate['H8'])
    p300.drop_tip()

    # H9: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H9'])
    p300.blow_out(plate['H9'])
    p300.drop_tip()

    # H2: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H2'])
    p300.blow_out(plate['H2'])
    p300.drop_tip()

    # H3: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H3'])
    p300.blow_out(plate['H3'])
    p300.drop_tip()

    # H4: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H4'])
    p300.blow_out(plate['H4'])
    p300.drop_tip()

    # H11: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H11'])
    p300.blow_out(plate['H11'])
    p300.drop_tip()

    # H10: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H10'])
    p300.blow_out(plate['H10'])
    p300.drop_tip()

    # H12: Controle | 50.0 uL | LED 0s
    p300.pick_up_tip()
    p300.aspirate(50.0, reservoir['A1'])
    p300.dispense(50.0, plate['H12'])
    p300.blow_out(plate['H12'])
    p300.drop_tip()

    # A8: Ulnar_Humano | 66.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(66.0, reservoir['A1'])
    p300.dispense(66.0, plate['A8'])
    p300.aspirate(50, plate['A8'])
    p300.dispense(50, plate['A8'])
    p300.aspirate(50, plate['A8'])
    p300.dispense(50, plate['A8'])
    p300.aspirate(50, plate['A8'])
    p300.dispense(50, plate['A8'])
    p300.blow_out(plate['A8'])
    p300.drop_tip()
    # Photopolymerize A8: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A7: Ulnar_Humano | 66.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(66.0, reservoir['A1'])
    p300.dispense(66.0, plate['A7'])
    p300.aspirate(50, plate['A7'])
    p300.dispense(50, plate['A7'])
    p300.aspirate(50, plate['A7'])
    p300.dispense(50, plate['A7'])
    p300.aspirate(50, plate['A7'])
    p300.dispense(50, plate['A7'])
    p300.blow_out(plate['A7'])
    p300.drop_tip()
    # Photopolymerize A7: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A9: Ulnar_Humano | 66.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(66.0, reservoir['A1'])
    p300.dispense(66.0, plate['A9'])
    p300.aspirate(50, plate['A9'])
    p300.dispense(50, plate['A9'])
    p300.aspirate(50, plate['A9'])
    p300.dispense(50, plate['A9'])
    p300.aspirate(50, plate['A9'])
    p300.dispense(50, plate['A9'])
    p300.blow_out(plate['A9'])
    p300.drop_tip()
    # Photopolymerize A9: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A6: Mediano_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['A6'])
    p300.aspirate(50, plate['A6'])
    p300.dispense(50, plate['A6'])
    p300.aspirate(50, plate['A6'])
    p300.dispense(50, plate['A6'])
    p300.aspirate(50, plate['A6'])
    p300.dispense(50, plate['A6'])
    p300.blow_out(plate['A6'])
    p300.drop_tip()
    # Photopolymerize A6: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A4: Mediano_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['A4'])
    p300.aspirate(50, plate['A4'])
    p300.dispense(50, plate['A4'])
    p300.aspirate(50, plate['A4'])
    p300.dispense(50, plate['A4'])
    p300.aspirate(50, plate['A4'])
    p300.dispense(50, plate['A4'])
    p300.blow_out(plate['A4'])
    p300.drop_tip()
    # Photopolymerize A4: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B7: Peroneiro_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['B7'])
    p300.aspirate(50, plate['B7'])
    p300.dispense(50, plate['B7'])
    p300.aspirate(50, plate['B7'])
    p300.dispense(50, plate['B7'])
    p300.aspirate(50, plate['B7'])
    p300.dispense(50, plate['B7'])
    p300.blow_out(plate['B7'])
    p300.drop_tip()
    # Photopolymerize B7: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B9: Peroneiro_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['B9'])
    p300.aspirate(50, plate['B9'])
    p300.dispense(50, plate['B9'])
    p300.aspirate(50, plate['B9'])
    p300.dispense(50, plate['B9'])
    p300.aspirate(50, plate['B9'])
    p300.dispense(50, plate['B9'])
    p300.blow_out(plate['B9'])
    p300.drop_tip()
    # Photopolymerize B9: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B8: Peroneiro_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['B8'])
    p300.aspirate(50, plate['B8'])
    p300.dispense(50, plate['B8'])
    p300.aspirate(50, plate['B8'])
    p300.dispense(50, plate['B8'])
    p300.aspirate(50, plate['B8'])
    p300.dispense(50, plate['B8'])
    p300.blow_out(plate['B8'])
    p300.drop_tip()
    # Photopolymerize B8: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A5: Mediano_Humano | 88.0 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(88.0, reservoir['A1'])
    p300.dispense(88.0, plate['A5'])
    p300.aspirate(50, plate['A5'])
    p300.dispense(50, plate['A5'])
    p300.aspirate(50, plate['A5'])
    p300.dispense(50, plate['A5'])
    p300.aspirate(50, plate['A5'])
    p300.dispense(50, plate['A5'])
    p300.blow_out(plate['A5'])
    p300.drop_tip()
    # Photopolymerize A5: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B4: Radial_Humano | 113.1 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(113.1, reservoir['A1'])
    p300.dispense(113.1, plate['B4'])
    p300.aspirate(50, plate['B4'])
    p300.dispense(50, plate['B4'])
    p300.aspirate(50, plate['B4'])
    p300.dispense(50, plate['B4'])
    p300.aspirate(50, plate['B4'])
    p300.dispense(50, plate['B4'])
    p300.blow_out(plate['B4'])
    p300.drop_tip()
    # Photopolymerize B4: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B5: Radial_Humano | 113.1 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(113.1, reservoir['A1'])
    p300.dispense(113.1, plate['B5'])
    p300.aspirate(50, plate['B5'])
    p300.dispense(50, plate['B5'])
    p300.aspirate(50, plate['B5'])
    p300.dispense(50, plate['B5'])
    p300.aspirate(50, plate['B5'])
    p300.dispense(50, plate['B5'])
    p300.blow_out(plate['B5'])
    p300.drop_tip()
    # Photopolymerize B5: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B6: Radial_Humano | 113.1 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(113.1, reservoir['A1'])
    p300.dispense(113.1, plate['B6'])
    p300.aspirate(50, plate['B6'])
    p300.dispense(50, plate['B6'])
    p300.aspirate(50, plate['B6'])
    p300.dispense(50, plate['B6'])
    p300.aspirate(50, plate['B6'])
    p300.dispense(50, plate['B6'])
    p300.blow_out(plate['B6'])
    p300.drop_tip()
    # Photopolymerize B6: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # A11: Femoral_Humano | 148.4 uL | LED 20s
    p300.pick_up_tip()
    p300.aspirate(148.4, reservoir['A1'])
    p300.dispense(148.4, plate['A11'])
    p300.aspirate(50, plate['A11'])
    p300.dispense(50, plate['A11'])
    p300.aspirate(50, plate['A11'])
    p300.dispense(50, plate['A11'])
    p300.aspirate(50, plate['A11'])
    p300.dispense(50, plate['A11'])
    p300.blow_out(plate['A11'])
    p300.drop_tip()
    # Photopolymerize A11: 405nm, 20s
    led_module.engage()  # LED ON
    protocol.delay(seconds=20.0)
    led_module.disengage()  # LED OFF

    # A10: Femoral_Humano | 148.4 uL | LED 20s
    p300.pick_up_tip()
    p300.aspirate(148.4, reservoir['A1'])
    p300.dispense(148.4, plate['A10'])
    p300.aspirate(50, plate['A10'])
    p300.dispense(50, plate['A10'])
    p300.aspirate(50, plate['A10'])
    p300.dispense(50, plate['A10'])
    p300.aspirate(50, plate['A10'])
    p300.dispense(50, plate['A10'])
    p300.blow_out(plate['A10'])
    p300.drop_tip()
    # Photopolymerize A10: 405nm, 20s
    led_module.engage()  # LED ON
    protocol.delay(seconds=20.0)
    led_module.disengage()  # LED OFF

    # A12: Femoral_Humano | 148.4 uL | LED 20s
    p300.pick_up_tip()
    p300.aspirate(148.4, reservoir['A1'])
    p300.dispense(148.4, plate['A12'])
    p300.aspirate(50, plate['A12'])
    p300.dispense(50, plate['A12'])
    p300.aspirate(50, plate['A12'])
    p300.dispense(50, plate['A12'])
    p300.aspirate(50, plate['A12'])
    p300.dispense(50, plate['A12'])
    p300.blow_out(plate['A12'])
    p300.drop_tip()
    # Photopolymerize A12: 405nm, 20s
    led_module.engage()  # LED ON
    protocol.delay(seconds=20.0)
    led_module.disengage()  # LED OFF

    # B1: Tibial_Humano | 204.2 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(204.2, reservoir['A1'])
    p300.dispense(204.2, plate['B1'])
    p300.aspirate(50, plate['B1'])
    p300.dispense(50, plate['B1'])
    p300.aspirate(50, plate['B1'])
    p300.dispense(50, plate['B1'])
    p300.aspirate(50, plate['B1'])
    p300.dispense(50, plate['B1'])
    p300.blow_out(plate['B1'])
    p300.drop_tip()
    # Photopolymerize B1: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B2: Tibial_Humano | 204.2 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(204.2, reservoir['A1'])
    p300.dispense(204.2, plate['B2'])
    p300.aspirate(50, plate['B2'])
    p300.dispense(50, plate['B2'])
    p300.aspirate(50, plate['B2'])
    p300.dispense(50, plate['B2'])
    p300.aspirate(50, plate['B2'])
    p300.dispense(50, plate['B2'])
    p300.blow_out(plate['B2'])
    p300.drop_tip()
    # Photopolymerize B2: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B3: Tibial_Humano | 204.2 uL | LED 15s
    p300.pick_up_tip()
    p300.aspirate(204.2, reservoir['A1'])
    p300.dispense(204.2, plate['B3'])
    p300.aspirate(50, plate['B3'])
    p300.dispense(50, plate['B3'])
    p300.aspirate(50, plate['B3'])
    p300.dispense(50, plate['B3'])
    p300.aspirate(50, plate['B3'])
    p300.dispense(50, plate['B3'])
    p300.blow_out(plate['B3'])
    p300.drop_tip()
    # Photopolymerize B3: 405nm, 15s
    led_module.engage()  # LED ON
    protocol.delay(seconds=15.0)
    led_module.disengage()  # LED OFF

    # B10: Ciatico_Humano | 259.2 uL | LED 25s
    p300.pick_up_tip()
    p300.aspirate(259.2, reservoir['A1'])
    p300.dispense(259.2, plate['B10'])
    p300.aspirate(50, plate['B10'])
    p300.dispense(50, plate['B10'])
    p300.aspirate(50, plate['B10'])
    p300.dispense(50, plate['B10'])
    p300.aspirate(50, plate['B10'])
    p300.dispense(50, plate['B10'])
    p300.blow_out(plate['B10'])
    p300.drop_tip()
    # Photopolymerize B10: 405nm, 25s
    led_module.engage()  # LED ON
    protocol.delay(seconds=25.0)
    led_module.disengage()  # LED OFF

    # B11: Ciatico_Humano | 259.2 uL | LED 25s
    p300.pick_up_tip()
    p300.aspirate(259.2, reservoir['A1'])
    p300.dispense(259.2, plate['B11'])
    p300.aspirate(50, plate['B11'])
    p300.dispense(50, plate['B11'])
    p300.aspirate(50, plate['B11'])
    p300.dispense(50, plate['B11'])
    p300.aspirate(50, plate['B11'])
    p300.dispense(50, plate['B11'])
    p300.blow_out(plate['B11'])
    p300.drop_tip()
    # Photopolymerize B11: 405nm, 25s
    led_module.engage()  # LED ON
    protocol.delay(seconds=25.0)
    led_module.disengage()  # LED OFF

    # B12: Ciatico_Humano | 259.2 uL | LED 25s
    p300.pick_up_tip()
    p300.aspirate(259.2, reservoir['A1'])
    p300.dispense(259.2, plate['B12'])
    p300.aspirate(50, plate['B12'])
    p300.dispense(50, plate['B12'])
    p300.aspirate(50, plate['B12'])
    p300.dispense(50, plate['B12'])
    p300.aspirate(50, plate['B12'])
    p300.dispense(50, plate['B12'])
    p300.blow_out(plate['B12'])
    p300.drop_tip()
    # Photopolymerize B12: 405nm, 25s
    led_module.engage()  # LED ON
    protocol.delay(seconds=25.0)
    led_module.disengage()  # LED OFF

    # Post-cure cooling wait
    protocol.delay(seconds=90.0)

    protocol.comment('Arkhe-Chain: 847.688')
