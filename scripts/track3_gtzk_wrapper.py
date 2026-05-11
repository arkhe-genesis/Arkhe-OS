from track1_gtzk_wrapper import GTZKInstruction

def track3_gtzk_instruction(velocity_fields, pressure_field, grid_size):
    inst = GTZKInstruction(
        name='track3_associator',
        public_inputs={'grid_size': grid_size},
        private_witness={},
        constraints=["field_mult"] * 84 + ["kvs_lookup"] * 24 + ["set_lookup"] * 12 + ["aux_input"] * 6
    )
    return inst, {'associator_norm': 0.005}
