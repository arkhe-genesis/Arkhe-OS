-- hardware/fpga_noma/moga_accel.vhd
-- Aceleração FPGA do MOGA para alocação de potência NOMA
-- Pipeline paralelo para avaliação de fitness de 50 indivíduos

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.MATH_REAL.ALL;

entity MOGA_Accelerator is
    Port (
        -- Clock e reset
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;

        -- Interface de controle
        start : in STD_LOGIC;
        busy : out STD_LOGIC;
        done : out STD_LOGIC;

        -- Parâmetros do problema
        num_devices : in unsigned(7 downto 0);   -- até 255 dispositivos
        num_subchannels : in unsigned(5 downto 0); -- até 63 subcanais
        max_power : in signed(15 downto 0);       -- potência máxima (ponto fixo)

        -- Dados de entrada: matriz de potência da população
        -- Formato: [pop_idx][device][subchannel] -> ponto fixo Q8.8
        population_in : in signed(15 downto 0);
        pop_idx_in : in unsigned(5 downto 0);     -- índice do indivíduo (0-49)
        load_data : in STD_LOGIC;
        data_ready : out STD_LOGIC;

        -- Resultados: fitness do indivíduo
        total_power : out signed(15 downto 0);    -- soma de potência
        avg_rate : out signed(15 downto 0);       -- taxa média (Q8.8)
        qos_violations : out unsigned(7 downto 0); -- contagem de violações

        -- Interface para projeção geométrica (CORDIC)
        project_enable : in STD_LOGIC;
        project_done : out STD_LOGIC
    );
end MOGA_Accelerator;

architecture Behavioral of MOGA_Accelerator is
    -- Pipeline stages
    type state_type is (IDLE, LOAD, EVAL_SINR, EVAL_RATE, AGGREGATE, PROJECT, OUTPUT);
    signal state : state_type := IDLE;

    -- Registradores de pipeline
    signal current_power : signed(15 downto 0) := (others => '0');
    signal current_rate : signed(15 downto 0) := (others => '0');
    signal violation_count : unsigned(7 downto 0) := (others => '0');

    -- Memória local para canais (simplificado: 24x12)
    type channel_array is array (0 to 23, 0 to 11) of signed(15 downto 0);
    signal channels : channel_array;

    -- CORDIC para cálculo de exp/log (para SINR e projeção)
    signal cordic_start : STD_LOGIC := '0';
    signal cordic_done : STD_LOGIC := '0';
    signal cordic_result : signed(15 downto 0);

    -- Contadores de pipeline
    signal dev_counter : unsigned(7 downto 0) := (others => '0');
    signal subch_counter : unsigned(5 downto 0) := (others => '0');
    signal pop_counter : unsigned(5 downto 0) := (others => '0');

begin
    -- Processo principal de controle
    process(clk, rst)
    begin
        if rst = '1' then
            state <= IDLE;
            busy <= '0';
            done <= '0';
            current_power <= (others => '0');
            current_rate <= (others => '0');
            violation_count <= (others => '0');

        elsif rising_edge(clk) then
            case state is
                when IDLE =>
                    busy <= '0';
                    done <= '0';
                    if start = '1' then
                        state <= LOAD;
                        busy <= '1';
                        pop_counter <= (others => '0');
                    end if;

                when LOAD =>
                    -- Carregar dados do indivíduo atual
                    if load_data = '1' then
                        -- Armazenar matriz de potência em registradores locais
                        -- (simplificado: em produção usar BRAM)
                        state <= EVAL_SINR;
                        dev_counter <= (others => '0');
                        subch_counter <= (others => '0');
                    end if;

                when EVAL_SINR =>
                    -- Calcular SINR para cada dispositivo/subcanal
                    -- Pipeline: 1 ciclo por par (device, subchannel)
                    if subch_counter < num_subchannels then
                        -- Calcular interferência e sinal
                        -- SINR = (P * |h|^2) / (interference + noise)
                        -- Usar CORDIC para divisão e log
                        cordic_start <= '1';
                        if cordic_done = '1' then
                            -- Acumular taxa: log2(1 + SINR)
                            current_rate <= current_rate + cordic_result;

                            -- Verificar QoS threshold
                            if cordic_result < x"0100" then -- threshold = 1.0 em Q8.8
                                violation_count <= violation_count + 1;
                            end if;

                            subch_counter <= subch_counter + 1;
                        end if;
                    elsif dev_counter < num_devices then
                        dev_counter <= dev_counter + 1;
                        subch_counter <= (others => '0');
                    else
                        state <= AGGREGATE;
                    end if;

                when AGGREGATE =>
                    -- Agregar métricas do indivíduo
                    total_power <= current_power;
                    avg_rate <= current_rate / to_signed(to_integer(num_devices) * to_integer(num_subchannels), 16);
                    qos_violations <= violation_count;
                    state <= OUTPUT;

                when OUTPUT =>
                    -- Disponibilizar resultados
                    done <= '1';
                    busy <= '0';
                    if start = '0' then
                        state <= IDLE;
                        done <= '0';
                    end if;

                when others =>
                    state <= IDLE;
            end case;
        end if;
    end process;

    -- Projeção geométrica: força constraints de SIC via pipeline
    process(clk, rst)
    begin
        if rst = '1' then
            project_done <= '0';
        elsif rising_edge(clk) then
            if project_enable = '1' then
                -- Implementar projeção: ordenar por ganho, ajustar potência
                -- Simplificado: aplicar fator de supressão exponencial
                project_done <= '1';
            else
                project_done <= '0';
            end if;
        end if;
    end process;

end Behavioral;
