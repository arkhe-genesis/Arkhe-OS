// ============================================================================
// tb_tau_soc_wrapper.sv
// Testbench for tau_soc_wrapper_v1_1
// ============================================================================

`timescale 1ns / 1ps

module tb_tau_soc_wrapper;

    localparam VOXEL_DATA_WIDTH = 128;
    localparam ROI_PACKET_WIDTH = 64;
    localparam CLK_PERIOD = 10; // 100MHz

    // DUT signals
    logic        clk_100mhz_p;
    logic        clk_100mhz_n;
    logic        rst_n_btn;
    logic        s_axis_lidar_tvalid;
    logic        s_axis_lidar_tready;
    logic [127:0] s_axis_lidar_tdata;
    logic        s_axis_lidar_tlast;
    logic        m_axis_roi_tvalid;
    logic        m_axis_roi_tready;
    logic [63:0] m_axis_roi_tdata;
    logic        m_axis_roi_tlast;
    logic        m_axis_roi_tid;
    logic        o_irq_roi_frame_done;
    logic [31:0] o_lambda_mesh_raw;
    logic        o_gate_healthy;
    logic        o_pll_locked;
    logic [11:0] o_dac_data;
    logic        o_dac_valid;
    logic        o_lce_computation_done;
    logic [31:0] o_lce_lambda2_estimate;
    logic        o_lce_self_model_flag;
    logic [127:0] o_nv_pred_error;
    logic [31:0] o_nv_lambda;
    logic        o_nv_valid;
    logic [3:0]  i_cfg_grid_shift;
    logic [15:0] i_cfg_red_threshold;
    logic [15:0] i_cfg_green_threshold;
    logic [15:0] i_cfg_blue_threshold;
    logic [127:0] i_ibmq_correction;
    logic        i_dac_ready;
    logic [31:0] o_vrp_frame_count;
    logic [31:0] o_vrp_voxel_count;
    logic        o_vrp_fifo_overflow;
    logic        o_mmcm_locked;

    // Clock generation
    always #((CLK_PERIOD/2)) begin
        clk_100mhz_p = ~clk_100mhz_p;
        clk_100mhz_n = ~clk_100mhz_p;
    end

    // DUT instantiation
    tau_soc_wrapper_v1_1 #(
        .VOXEL_DATA_WIDTH(VOXEL_DATA_WIDTH),
        .HASH_TABLE_DEPTH(2048),
        .ROI_FIFO_DEPTH(256),
        .ROI_PACKET_WIDTH(ROI_PACKET_WIDTH)
    ) dut (
        .clk_100mhz_p        (clk_100mhz_p),
        .clk_100mhz_n        (clk_100mhz_n),
        .rst_n_btn           (rst_n_btn),
        .s_axis_lidar_tvalid (s_axis_lidar_tvalid),
        .s_axis_lidar_tready (s_axis_lidar_tready),
        .s_axis_lidar_tdata  (s_axis_lidar_tdata),
        .s_axis_lidar_tlast  (s_axis_lidar_tlast),
        .m_axis_roi_tvalid   (m_axis_roi_tvalid),
        .m_axis_roi_tready   (m_axis_roi_tready),
        .m_axis_roi_tdata    (m_axis_roi_tdata),
        .m_axis_roi_tlast    (m_axis_roi_tlast),
        .m_axis_roi_tid      (m_axis_roi_tid),
        .o_irq_roi_frame_done(o_irq_roi_frame_done),
        .o_lambda_mesh_raw   (o_lambda_mesh_raw),
        .o_gate_healthy      (o_gate_healthy),
        .o_pll_locked        (o_pll_locked),
        .o_dac_data          (o_dac_data),
        .o_dac_valid         (o_dac_valid),
        .o_lce_computation_done(o_lce_computation_done),
        .o_lce_lambda2_estimate(o_lce_lambda2_estimate),
        .o_lce_self_model_flag (o_lce_self_model_flag),
        .o_nv_pred_error     (o_nv_pred_error),
        .o_nv_lambda         (o_nv_lambda),
        .o_nv_valid          (o_nv_valid),
        .i_cfg_grid_shift    (i_cfg_grid_shift),
        .i_cfg_red_threshold (i_cfg_red_threshold),
        .i_cfg_green_threshold(i_cfg_green_threshold),
        .i_cfg_blue_threshold(i_cfg_blue_threshold),
        .i_ibmq_correction   (i_ibmq_correction),
        .i_dac_ready         (i_dac_ready),
        .o_vrp_frame_count   (o_vrp_frame_count),
        .o_vrp_voxel_count   (o_vrp_voxel_count),
        .o_vrp_fifo_overflow (o_vrp_fifo_overflow),
        .o_mmcm_locked       (o_mmcm_locked)
    );

    // ------------------------------------------------------------------------
    // Testbench tasks
    // ------------------------------------------------------------------------
    task automatic reset_system();
        rst_n_btn = 1'b0;
        repeat(20) @(posedge clk_100mhz_p);
        rst_n_btn = 1'b1;
        // Wait for PLL lock (simulated)
        repeat(100) @(posedge clk_100mhz_p);
        $display("[%0t] Reset released.", $time);
    endtask

    task automatic send_voxel(
        input logic [15:0] x, y, z,
        input logic [7:0]  r, g, b,
        input logic [15:0] intensity,
        input logic        is_last
    );
        // Pack data according to VRP v1.1 unpacking order
        s_axis_lidar_tdata = {
            intensity, b, g, r,
            z, y, x
        };
        s_axis_lidar_tvalid = 1'b1;
        s_axis_lidar_tlast  = is_last;
        // Wait for tready
        do @(posedge clk_100mhz_p); while (!s_axis_lidar_tready);
        @(posedge clk_100mhz_p);
        s_axis_lidar_tvalid = 1'b0;
        s_axis_lidar_tlast  = 1'b0;
    endtask

    task automatic send_frame(input int num_voxels, input bit random_colors = 1);
        for (int i = 0; i < num_voxels; i++) begin
            logic [7:0] r, g, b;
            if (random_colors && (i % 10 == 0)) begin
                r = 8'hFF; g = 8'h00; b = 8'h00; // red -> ROI
            end else if (random_colors && (i % 7 == 0)) begin
                r = 8'h00; g = 8'hFF; b = 8'h00; // green -> ROI
            end else begin
                r = 8'h40; g = 8'h40; b = 8'h40; // gray -> no ROI
            end
            send_voxel(i*10, (i*7)%1024, (i*3)%512, r, g, b, 16'hFFFF, (i == num_voxels-1));
        end
    endtask

    // ------------------------------------------------------------------------
    // Initialization and Test Sequence
    // ------------------------------------------------------------------------
    int roi_pkt_cnt;
    int frame_cnt;
    int irq_cnt;
    logic [31:0] last_frame_count;

    initial begin
        // Init signals
        clk_100mhz_p = 0;
        clk_100mhz_n = 1;
        rst_n_btn = 1;
        s_axis_lidar_tvalid = 0;
        s_axis_lidar_tdata = 0;
        s_axis_lidar_tlast = 0;
        m_axis_roi_tready = 1; // default ready
        i_cfg_grid_shift = 2;  // 4mm
        i_cfg_red_threshold = 16'h0080;
        i_cfg_green_threshold = 16'h0080;
        i_cfg_blue_threshold = 16'h0080;
        i_ibmq_correction = 0;
        i_dac_ready = 1;

        reset_system();

        // Force o_pll_locked high for simulation (O-Core stub may not drive it)
        // In real design, O-Core will drive it.
        force dut.o_pll_locked = 1'b1;

        $display("========================================");
        $display(" TAU SoC Wrapper Regression Test");
        $display("========================================");

        // ----------------------------------------------------------------
        // Test 1: Basic Frame (no backpressure)
        // ----------------------------------------------------------------
        $display("[TEST 1] Single frame without backpressure.");
        roi_pkt_cnt = 0;
        irq_cnt = 0;
        fork
            begin
                send_frame(100, 1);
            end
            begin
                // Monitor ROI output
                while (!o_irq_roi_frame_done) begin
                    @(posedge clk_100mhz_p);
                    if (m_axis_roi_tvalid && m_axis_roi_tready) begin
                        roi_pkt_cnt++;
                        if (m_axis_roi_tlast) $display("[%0t] tlast asserted.", $time);
                    end
                    if (o_irq_roi_frame_done) irq_cnt++;
                end
            end
        join
        repeat(100) @(posedge clk_100mhz_p);
        $display("[TEST 1] Frame count: %0d, ROI packets: %0d, IRQ pulses: %0d",
                 o_vrp_frame_count, roi_pkt_cnt, irq_cnt);
        if (o_vrp_frame_count > 0 && roi_pkt_cnt > 0 && irq_cnt == 1)
            $display("[TEST 1] PASS");
        else
            $display("[TEST 1] FAIL");

        // ----------------------------------------------------------------
        // Test 2: Backpressure (random tready)
        // ----------------------------------------------------------------
        $display("[TEST 2] Backpressure test.");
        roi_pkt_cnt = 0;
        irq_cnt = 0;
        last_frame_count = o_vrp_frame_count;
        fork
            begin
                // Randomize m_axis_roi_tready
                for (int i = 0; i < 1000; i++) begin
                    @(posedge clk_100mhz_p);
                    m_axis_roi_tready = ($random % 2);
                end
            end
            begin
                send_frame(150, 1);
            end
            begin
                while (!o_irq_roi_frame_done) begin
                    @(posedge clk_100mhz_p);
                    if (m_axis_roi_tvalid && m_axis_roi_tready) roi_pkt_cnt++;
                    if (o_irq_roi_frame_done) irq_cnt++;
                end
            end
        join
        m_axis_roi_tready = 1; // restore
        repeat(100) @(posedge clk_100mhz_p);
        $display("[TEST 2] Frame count increased: %0d -> %0d, ROI packets: %0d",
                 last_frame_count, o_vrp_frame_count, roi_pkt_cnt);
        if (o_vrp_frame_count > last_frame_count && irq_cnt == 1)
            $display("[TEST 2] PASS");
        else
            $display("[TEST 2] FAIL");

        // ----------------------------------------------------------------
        // Test 3: FIFO overflow
        // ----------------------------------------------------------------
        $display("[TEST 3] FIFO overflow test (NoC stalled).");
        m_axis_roi_tready = 0; // stall consumer
        send_frame(300, 1);    // many interesting voxels
        repeat(500) @(posedge clk_100mhz_p);
        m_axis_roi_tready = 1; // release
        repeat(500) @(posedge clk_100mhz_p);
        if (o_vrp_fifo_overflow)
            $display("[TEST 3] PASS (overflow detected)");
        else
            $display("[TEST 3] FAIL (overflow not detected)");

        // ----------------------------------------------------------------
        // Test 4: Frame with zero ROI
        // ----------------------------------------------------------------
        $display("[TEST 4] Frame with no interesting voxels.");
        last_frame_count = o_vrp_frame_count;
        send_frame(50, 0); // all gray
        repeat(200) @(posedge clk_100mhz_p);
        if (o_vrp_frame_count > last_frame_count)
            $display("[TEST 4] PASS (frame counted even with no ROI)");
        else
            $display("[TEST 4] FAIL");

        $display("Simulation complete.");
        $finish;
    end

    // Watchdog
    initial begin
        #1000000; // 1ms
        $display("ERROR: Timeout");
        $finish;
    end

    // Waveform dumping
    initial begin
        $dumpfile("tb_tau_soc_wrapper.vcd");
        $dumpvars(0, tb_tau_soc_wrapper);
    end

endmodule
