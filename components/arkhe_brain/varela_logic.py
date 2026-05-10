"""
Varela Ternary Logic (0, 1, 'a') for CorvOS
Implements the Calculus for Self-Reference (Spencer-Brown / Francisco Varela)
for the Arkhe(n) Project.
"""

import numpy as np
from dataclasses import dataclass
from typing import Union, Dict

class VarelaState:
    UNMARKED = 0
    MARKED = 1
    AUTONOMOUS = 'a'

class VarelaLogic:
    """
    Implements the core operations of Varela's ternary logic.
    - 0 (Void/Unmarked)
    - 1 (Marked)
    - a (Autonomous/Coherent)
    """

    @staticmethod
    def cross(state: Union[int, str]) -> Union[int, str]:
        """
        The 'cross' operator (inversion).
        - cross(0) = 1
        - cross(1) = 0
        - cross(a) = a  (Self-referential identity)
        """
        if state == VarelaState.UNMARKED:
            return VarelaState.MARKED
        elif state == VarelaState.MARKED:
            return VarelaState.UNMARKED
        elif state == VarelaState.AUTONOMOUS:
            return VarelaState.AUTONOMOUS
        else:
            raise ValueError(f"Invalid Varela state: {state}")

    @staticmethod
    def call(state1: Union[int, str], state2: Union[int, str]) -> Union[int, str]:
        """
        The 'call' operator (juxtaposition).
        If either is marked, the result is marked, unless autonomous.
        Autonomous ('a') dominates when paired with 0 or 1 in re-entry loops.
        """
        # Simplification of juxtaposition for qhttp handshake
        if state1 == VarelaState.AUTONOMOUS or state2 == VarelaState.AUTONOMOUS:
            return VarelaState.AUTONOMOUS
        if state1 == VarelaState.MARKED or state2 == VarelaState.MARKED:
            return VarelaState.MARKED
        return VarelaState.UNMARKED

    @staticmethod
    def re_entry_handshake(incoming_state: Union[int, str], local_phase: float) -> Dict:
        """
        Logic for the qhttp re-entry handshake.
        If incoming is 'a', the system enters resonance.
        """
        result = {
            "output_state": VarelaState.UNMARKED,
            "resonance_active": False,
            "phase_shift": 0.0
        }

        if incoming_state == VarelaState.AUTONOMOUS:
            result["output_state"] = VarelaState.AUTONOMOUS
            result["resonance_active"] = True
            # Resonance logic: minimize phase difference
            result["phase_shift"] = np.pi / 13 # Twist from the 13-node ring
        elif incoming_state == VarelaState.MARKED:
            result["output_state"] = VarelaState.UNMARKED # Traditional ACK flip
        else:
            result["output_state"] = VarelaState.MARKED # Wake up from void

        return result

if __name__ == "__main__":
    # Quick test
    logic = VarelaLogic()
    print(f"cross(0) = {logic.cross(0)}")
    print(f"cross(1) = {logic.cross(1)}")
    print(f"cross('a') = {logic.cross('a')}")
    print(f"call(1, 0) = {logic.call(1, 0)}")
    print(f"call('a', 1) = {logic.call('a', 1)}")
    print(f"Handshake 'a': {logic.re_entry_handshake('a', 0.847)}")
