//=============================================================================
// ARKHE VEI v0.2 — Mesh Controller
//=============================================================================

module mesh_controller #(
    parameter int CLK_FREQ_HZ = 1_000_000
) (
    input  logic         clk,
    input  logic         rst_n,

    input  logic [15:0]  lambda_mesh_raw,
    input  logic [15:0]  lambda_min,
    input  logic [15:0]  lambda_target,
    input  logic         gate_healthy,

    output logic         ibmq_update_req,
    output logic         pau_enable,
    output logic         pau_apply_correction,
    output logic         dac_update_strobe,
    output logic         alert_decoherence,
    output logic         alert_gate_critical
);

    typedef enum logic [2:0] {
        ST_RESET       = 3'b000,
        ST_IDLE        = 3'b001,
        ST_CALIBRATING = 3'b010,
        ST_COHERENT    = 3'b011,
        ST_CRITICAL    = 3'b100,
        ST_DECOHERED   = 3'b101
    } state_t;

    state_t state, next_state;

    // Máquina de estados (Correção P6: Reset de next_state)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_RESET;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        pau_enable = 1'b0;
        pau_apply_correction = 1'b0;
        ibmq_update_req = 1'b0;
        alert_decoherence = 1'b0;
        alert_gate_critical = 1'b0;
        dac_update_strobe = 1'b0;

        case (state)
            ST_RESET: begin
                next_state = ST_IDLE;
            end

            ST_IDLE: begin
                if (gate_healthy) next_state = ST_CALIBRATING;
            end

            ST_CALIBRATING: begin
                pau_enable = 1'b1;
                if (!gate_healthy) begin
                    next_state = ST_IDLE;
                    alert_gate_critical = 1'b1;
                end else if (lambda_mesh_raw >= lambda_min) begin
                    next_state = ST_COHERENT;
                end
            end

            ST_COHERENT: begin
                pau_enable = 1'b1;
                pau_apply_correction = 1'b1;
                dac_update_strobe = 1'b1;
                if (!gate_healthy) begin
                    next_state = ST_CRITICAL;
                    alert_gate_critical = 1'b1;
                end else if (lambda_mesh_raw < lambda_min) begin
                    next_state = ST_DECOHERED;
                    alert_decoherence = 1'b1;
                end else if (lambda_mesh_raw < lambda_target) begin
                    ibmq_update_req = 1'b1;
                end
            end

            ST_CRITICAL: begin
                alert_gate_critical = 1'b1;
                if (gate_healthy) next_state = ST_CALIBRATING;
                else next_state = ST_IDLE;
            end

            ST_DECOHERED: begin
                alert_decoherence = 1'b1;
                if (lambda_mesh_raw >= lambda_min) next_state = ST_COHERENT;
                else if (!gate_healthy) next_state = ST_IDLE;
            end

            default: next_state = ST_IDLE;
        endcase
    end

endmodule
