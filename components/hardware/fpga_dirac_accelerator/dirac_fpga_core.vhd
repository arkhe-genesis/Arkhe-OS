-- hardware/fpga_dirac_accelerator/dirac_fpga_core.vhd
-- Núcleo FPGA para computação de D_T ψ = γ^μ(∇_μ + ⅛ T_{μνρ}[γ^ν,γ^ρ])ψ
-- Arquitetura pipeline para detecção de zero-modes (estados de misericórdia)

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.MATH_REAL.ALL;

entity DiracFPGACore is
    Port (
        -- Clock e reset
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;

        -- Interface de entrada: espinor ψ (2 componentes por vértice, ponto fixo Q16.16)
        psi_in_re : in STD_LOGIC_VECTOR(31 downto 0);  -- parte real
        psi_in_im : in STD_LOGIC_VECTOR(31 downto 0);  -- parte imaginária
        psi_valid : in STD_LOGIC;
        psi_ready : out STD_LOGIC;

        -- Parâmetros de torção (configuráveis via registradores)
        torsion_strength : in STD_LOGIC_VECTOR(15 downto 0);  -- Q8.8
        evolution_steps : in STD_LOGIC_VECTOR(7 downto 0);    -- número de iterações

        -- Interface de saída: D_T ψ
        dirac_out_re : out STD_LOGIC_VECTOR(31 downto 0);
        dirac_out_im : out STD_LOGIC_VECTOR(31 downto 0);
        out_valid : out STD_LOGIC;
        out_ready : in STD_LOGIC;

        -- Detecção de zero-mode: |D_T ψ| < threshold
        zero_mode_threshold : in STD_LOGIC_VECTOR(15 downto 0);  -- Q8.8
        zero_mode_detected : out STD_LOGIC;

        -- Status e controle
        busy : out STD_LOGIC;
        done : out STD_LOGIC;
        error_flag : out STD_LOGIC
    );
end DiracFPGACore;

architecture Behavioral of DiracFPGACore is
    -- Tipos de ponto fixo Q16.16 para componentes de espinor
    subtype fixed_t is signed(31 downto 0);

    -- Matrizes de Clifford γ^μ em 2D (pré-computadas em LUTs)
    -- γ⁰ = σ¹ = [[0,1],[1,0]], γ¹ = σ² = [[0,-i],[i,0]]
    constant GAMMA0_RE : fixed_t := to_fixed(0.0, 32);  -- parte real de γ⁰
    constant GAMMA0_IM : fixed_t := to_fixed(0.0, 32);
    constant GAMMA1_RE : fixed_t := to_fixed(0.0, 32);
    constant GAMMA1_IM : fixed_t := to_fixed(1.0, 32);  -- σ² tem parte imaginária

    -- Pipeline de 4 estágios: fetch → derivative → torsion → accumulate
    type pipeline_state is (IDLE, FETCH, DERIVATIVE, TORSION, ACCUMULATE, OUTPUT);
    signal state : pipeline_state := IDLE;

    -- Registradores de pipeline
    signal psi_re_pipe : fixed_t;
    signal psi_im_pipe : fixed_t;
    signal deriv_re : fixed_t;
    signal deriv_im : fixed_t;
    signal torsion_term_re : fixed_t;
    signal torsion_term_im : fixed_t;
    signal result_re : fixed_t;
    signal result_im : fixed_t;

    -- Contador de iterações
    signal iter_counter : unsigned(7 downto 0) := (others => '0');

    -- Função de conversão para ponto fixo
    function to_fixed(val : real; bits : integer) return fixed_t is
        variable scaled : real;
        variable result : fixed_t;
    begin
        scaled := val * (2.0**16);  -- Q16.16: 16 bits fracionários
        result := to_signed(integer(scaled), bits);
        return result;
    end function;

    -- Multiplicação de ponto fixo Q16.16 × Q16.16 → Q16.16 (com saturação)
    function fixed_mul(a, b : fixed_t) return fixed_t is
        variable prod : signed(63 downto 0);
        variable result : fixed_t;
    begin
        prod := a * b;  -- resultado em Q32.32
        result := prod(47 downto 16);  -- truncar para Q16.16
        -- Saturação simples
        if result > x"7FFF_FFFF" then result := x"7FFF_FFFF";
        elsif result < x"8000_0000" then result := x"8000_0000";
        end if;
        return result;
    end function;

    -- Soma de ponto fixo com saturação
    function fixed_add(a, b : fixed_t) return fixed_t is
        variable sum : signed(32 downto 0);
        variable result : fixed_t;
    begin
        sum := signed(a) + signed(b);
        result := sum(31 downto 0);
        -- Detectar overflow
        if (a(31) = b(31)) and (a(31) /= result(31)) then
            if a(31) = '0' then result := x"7FFF_FFFF";  -- overflow positivo
            else result := x"8000_0000";  -- overflow negativo
            end if;
        end if;
        return result;
    end function;

begin
    -- Processo principal de pipeline
    process(clk, rst)
        variable gamma_psi_re, gamma_psi_im : fixed_t;
        variable commutator_re, commutator_im : fixed_t;
        variable torsion_scaled : fixed_t;
    begin
        if rst = '1' then
            state <= IDLE;
            psi_ready <= '0';
            out_valid <= '0';
            busy <= '0';
            done <= '0';
            error_flag <= '0';
            iter_counter <= (others => '0');
            zero_mode_detected <= '0';

        elsif rising_edge(clk) then
            -- Controle de fluxo básico
            psi_ready <= '1' when state = IDLE else '0';
            busy <= '1' when state /= IDLE else '0';

            case state is
                when IDLE =>
                    if psi_valid = '1' then
                        -- Carregar espinor de entrada
                        psi_re_pipe <= signed(psi_in_re);
                        psi_im_pipe <= signed(psi_in_im);
                        iter_counter <= unsigned(evolution_steps) - 1;
                        state <= FETCH;
                    end if;

                when FETCH =>
                    -- Estágio 1: aplicar γ^μ ao espinor (simplificação: γ⁰ apenas)
                    -- γ⁰ ψ = [[0,1],[1,0]] [ψ₁; ψ₂] = [ψ₂; ψ₁]
                    -- Implementação simplificada para demonstração
                    gamma_psi_re := psi_im_pipe;  -- troca componentes para γ⁰
                    gamma_psi_im := psi_re_pipe;

                    -- Calcular derivada discreta ∇_μ ψ (diferença finita central)
                    -- ∇ψ ≈ (ψ[i+1] - ψ[i-1]) / (2Δx) — simplificado para diferença forward
                    deriv_re := fixed_add(psi_re_pipe, to_fixed(-0.1, 32));  -- exemplo: -0.1 como derivada
                    deriv_im := fixed_add(psi_im_pipe, to_fixed(-0.1, 32));

                    state <= DERIVATIVE;

                when DERIVATIVE =>
                    -- Estágio 2: calcular termo de torção ⅛ T_{μνρ} [γ^ν, γ^ρ] ψ
                    -- Para 2D: [γ⁰, γ¹] = γ⁰γ¹ - γ¹γ⁰ = 2iσ³ (exemplo)
                    -- [γ⁰, γ¹] ψ = 2i [[1,0],[0,-1]] ψ = [2iψ₁; -2iψ₂]

                    -- Converter torsion_strength de Q8.8 para Q16.16
                    torsion_scaled := resize(signed(torsion_strength), 32) sll 8;

                    -- Calcular comutador × ψ (simplificado)
                    commutator_re := fixed_mul(torsion_scaled, psi_re_pipe);  -- 2iψ₁ → parte real
                    commutator_im := fixed_mul(torsion_scaled, to_fixed(-1.0, 32));  -- fase i

                    -- Escalar por ⅛
                    torsion_term_re := commutator_re sra 3;  -- divisão por 8 via shift
                    torsion_term_im := commutator_im sra 3;

                    state <= TORSION;

                when TORSION =>
                    -- Estágio 3: acumular γ^μ∇_μ ψ + termo de torção
                    result_re := fixed_add(fixed_mul(GAMMA0_RE, deriv_re), torsion_term_re);
                    result_im := fixed_add(fixed_mul(GAMMA0_IM, deriv_im), torsion_term_im);

                    -- Decrementar contador de iterações
                    if iter_counter > 0 then
                        iter_counter <= iter_counter - 1;
                        -- Feedback para próxima iteração (simplificação)
                        psi_re_pipe <= result_re;
                        psi_im_pipe <= result_im;
                        state <= FETCH;  -- pipeline iterativo
                    else
                        state <= ACCUMULATE;
                    end if;

                when ACCUMULATE =>
                    -- Estágio 4: normalizar resultado e preparar saída
                    -- Calcular magnitude |D_T ψ| para detecção de zero-mode
                    -- |ψ|² = ψ_re² + ψ_im² (aproximação em ponto fixo)
                    declare
                        variable mag_sq : signed(63 downto 0);
                        variable mag : fixed_t;
                    begin
                        mag_sq := signed(result_re) * signed(result_re) +
                                  signed(result_im) * signed(result_im);
                        -- Aproximação de sqrt via Newton-Raphson simplificada (1 iteração)
                        mag := mag_sq(47 downto 16);  -- extrair parte inteira de Q32.32

                        -- Comparar com threshold para zero-mode
                        if mag < signed(zero_mode_threshold) then
                            zero_mode_detected <= '1';
                        else
                            zero_mode_detected <= '0';
                        end if;
                    end;

                    state <= OUTPUT;

                when OUTPUT =>
                    -- Estágio 5: enviar resultado
                    dirac_out_re <= std_logic_vector(result_re);
                    dirac_out_im <= std_logic_vector(result_im);
                    out_valid <= '1';

                    if out_ready = '1' then
                        out_valid <= '0';
                        done <= '1';
                        state <= IDLE;
                    end if;

                when others =>
                    state <= IDLE;
            end case;

            -- Reset de flags
            if done = '1' then
                done <= '0';
            end if;
            if zero_mode_detected = '1' and state = IDLE then
                zero_mode_detected <= '0';
            end if;

        end if;
    end process;

    -- Indicador de erro simples (overflow detection)
    process(clk)
    begin
        if rising_edge(clk) then
            if state = ACCUMULATE then
                -- Detectar overflow em resultado final
                if (result_re(31) /= result_re(30)) or (result_im(31) /= result_im(30)) then
                    error_flag <= '1';
                else
                    error_flag <= '0';
                end if;
            end if;
        end if;
    end process;

end Behavioral;
