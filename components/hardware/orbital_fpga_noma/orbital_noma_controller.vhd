-- hardware/orbital_fpga_noma/orbital_noma_controller.vhd
-- Controlador FPGA para processamento NOMA em satélite LEO com handoff orbital

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity OrbitalNOMAController is
    Port (
        -- Clocks
        clk_sys : in STD_LOGIC;
        clk_orbital : in STD_LOGIC; -- clock sincronizado com órbita

        -- Interface SDR para captura de canais terrestres
        sdr_i_data : in STD_LOGIC_VECTOR(15 downto 0);
        sdr_q_data : in STD_LOGIC_VECTOR(15 downto 0);
        sdr_valid : in STD_LOGIC;
        sdr_ready : out STD_LOGIC;

        -- Interface MOGA accelerator (do módulo anterior)
        moga_start : out STD_LOGIC;
        moga_done : in STD_LOGIC;
        moga_result_valid : in STD_LOGIC;
        moga_power_alloc : in STD_LOGIC_VECTOR(255 downto 0); -- alocação de potência

        -- Interface inter-satellite link (emaranhamento quântico)
        isl_sync_pulse : in STD_LOGIC; -- pulso de sincronização de outros satélites
        isl_phase_correction : in STD_LOGIC_VECTOR(31 downto 0); -- correção de fase interestelar

        -- Interface downlink para dispositivos IoT
        downlink_data : out STD_LOGIC_VECTOR(127 downto 0);
        downlink_valid : out STD_LOGIC;
        downlink_ready : in STD_LOGIC;

        -- Controle orbital
        satellite_id : in STD_LOGIC_VECTOR(7 downto 0);
        orbital_position : in STD_LOGIC_VECTOR(63 downto 0); -- posição orbital codificada
        handoff_trigger : in STD_LOGIC; -- sinal para handoff para próximo satélite

        -- Status
        processing_complete : out STD_LOGIC;
        handoff_ready : out STD_LOGIC
    );
end OrbitalNOMAController;

architecture Behavioral of OrbitalNOMAController is
    -- Pipeline de processamento orbital
    type state_type is (IDLE, CAPTURE_CHANNELS, RUN_MOGA, APPLY_PHASE_CORRECTION,
                        PREPARE_DOWNLINK, HANDOFF_PREP, HANDOFF_EXEC);
    signal state : state_type := IDLE;

    -- Buffers para canais capturados
    signal channel_buffer : STD_LOGIC_VECTOR(511 downto 0); -- 8 dispositivos × 64 bits
    signal channels_valid : STD_LOGIC := '0';

    -- Correção de fase interestelar
    signal phase_correction_reg : STD_LOGIC_VECTOR(31 downto 0);

    -- Resultado do MOGA com correção orbital
    signal corrected_power_alloc : STD_LOGIC_VECTOR(255 downto 0);

    -- Controle de handoff
    signal handoff_pending : STD_LOGIC := '0';
    signal handoff_data_buffer : STD_LOGIC_VECTOR(255 downto 0);

    -- Contadores orbitais
    signal orbital_counter : unsigned(31 downto 0) := (others => '0');

begin
    -- Processo principal de controle orbital
    process(clk_sys, clk_orbital)
    begin
        if rising_edge(clk_sys) then
            case state is
                when IDLE =>
                    processing_complete <= '0';
                    handoff_ready <= '0';
                    sdr_ready <= '1';

                    if sdr_valid = '1' and channels_valid = '0' then
                        -- Capturar amostras I/Q do SDR
                        channel_buffer(15 downto 0) <= sdr_i_data;
                        channel_buffer(31 downto 16) <= sdr_q_data;
                        orbital_counter <= orbital_counter + 1;

                        if orbital_counter = 63 then
                            channels_valid <= '1';
                            orbital_counter <= (others => '0');
                            state <= RUN_MOGA;
                        end if;
                    end if;

                    -- Verificar trigger de handoff
                    if handoff_trigger = '1' then
                        handoff_pending <= '1';
                        state <= HANDOFF_PREP;
                    end if;

                when RUN_MOGA =>
                    if channels_valid = '1' then
                        -- Disparar acelerador MOGA
                        moga_start <= '1';
                        state <= APPLY_PHASE_CORRECTION;
                    end if;

                when APPLY_PHASE_CORRECTION =>
                    if moga_done = '1' then
                        -- Aplicar correção de fase interestelar à alocação
                        -- Simplificação: XOR com correção para demonstração
                        corrected_power_alloc <= moga_power_alloc xor
                            (phase_correction_reg & phase_correction_reg &
                             phase_correction_reg & phase_correction_reg &
                             phase_correction_reg & phase_correction_reg &
                             phase_correction_reg & phase_correction_reg);

                        phase_correction_reg <= isl_phase_correction;
                        state <= PREPARE_DOWNLINK;
                    end if;

                when PREPARE_DOWNLINK =>
                    -- Preparar pacote de downlink com alocação corrigida
                    downlink_data <= corrected_power_alloc(127 downto 0);
                    downlink_valid <= '1';

                    if downlink_ready = '1' then
                        downlink_valid <= '0';
                        processing_complete <= '1';

                        if handoff_pending = '1' then
                            state <= HANDOFF_EXEC;
                        else
                            state <= IDLE;
                            channels_valid <= '0';
                        end if;
                    end if;

                when HANDOFF_PREP =>
                    -- Bufferizar dados para handoff
                    handoff_data_buffer <= corrected_power_alloc;
                    handoff_ready <= '1';
                    state <= HANDOFF_EXEC;

                when HANDOFF_EXEC =>
                    -- Executar handoff para próximo satélite
                    -- Em produção: transmitir via inter-satellite link
                    if isl_sync_pulse = '1' then
                        -- Sincronizado com próximo satélite: transferir estado
                        handoff_pending <= '0';
                        handoff_ready <= '0';
                        state <= IDLE;
                        channels_valid <= '0';
                    end if;

                when others =>
                    state <= IDLE;
            end case;
        end if;

        -- Clock orbital para sincronização de fase
        if rising_edge(clk_orbital) then
            -- Atualizar correção de fase baseada em posição orbital
            -- Simplificação: correção proporcional à posição
            phase_correction_reg <= std_logic_vector(
                unsigned(phase_correction_reg) +
                unsigned(orbital_position(15 downto 0))
            );
        end if;
    end process;

    -- Reset de sinais
    process(clk_sys)
    begin
        if rising_edge(clk_sys) then
            if state = RUN_MOGA and moga_done = '1' then
                moga_start <= '0';
            end if;
        end if;
    end process;

end Behavioral;
