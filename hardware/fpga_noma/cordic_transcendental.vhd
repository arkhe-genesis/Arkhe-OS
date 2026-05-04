-- hardware/fpga_noma/cordic_transcendental.vhd
-- Módulo CORDIC para cálculo de exp(x), log(x), log2(1+x) em ponto fixo

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity CORDIC_Transcendental is
    Port (
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;
        start : in STD_LOGIC;
        done : out STD_LOGIC;

        -- Entrada: valor em ponto fixo Q8.8 (8 bits inteiro, 8 fracionário)
        input : in signed(15 downto 0);

        -- Saída: resultado em Q8.8
        result : out signed(15 downto 0);

        -- Seleção de operação: "00"=exp, "01"=log2(1+x), "10"=sqrt
        operation : in STD_LOGIC_VECTOR(1 downto 0)
    );
end CORDIC_Transcendental;

architecture Behavioral of CORDIC_Transcendental is
    -- Parâmetros CORDIC
    constant ITERATIONS : integer := 16;  -- precisão de 16 iterações
    constant Q_FORMAT : integer := 8;     -- bits fracionários

    -- Registradores de pipeline
    signal x_reg, y_reg, z_reg : signed(15 downto 0);
    signal iteration : integer range 0 to ITERATIONS := 0;
    signal op_reg : STD_LOGIC_VECTOR(1 downto 0);

    -- Tabelas de constantes pré-computadas (em ROM)
    type rom_type is array (0 to ITERATIONS-1) of signed(15 downto 0);

    -- Constantes para log2: atan(2^-i) em Q8.8
    constant ATAN_TABLE : rom_type := (
        x"1920", x"0CE9", x"067B", x"033D", x"019E", x"00CF", x"0067", x"0033",
        x"0019", x"000C", x"0006", x"0003", x"0001", x"0000", x"0000", x"0000"
    );

    -- Constantes para exp: log2(1+2^-i) em Q8.8
    constant LOG_TABLE : rom_type := (
        x"0100", x"00B2", x"0058", x"002C", x"0016", x"000B", x"0005", x"0002",
        x"0001", x"0000", x"0000", x"0000", x"0000", x"0000", x"0000", x"0000"
    );

    signal active : STD_LOGIC := '0';

begin
    process(clk, rst)
        variable x, y, z : signed(15 downto 0);
        variable x_next, y_next, z_next : signed(15 downto 0);
        variable direction : STD_LOGIC;
    begin
        if rst = '1' then
            active <= '0';
            done <= '0';
            iteration <= 0;
            result <= (others => '0');

        elsif rising_edge(clk) then
            if start = '1' and active = '0' then
                -- Iniciar nova operação
                active <= '1';
                iteration <= 0;
                op_reg <= operation;
                done <= '0';

                -- Inicializar registradores conforme operação
                case operation is
                    when "01" =>  -- log2(1+x)
                        x := input;  -- x = input
                        y := (others => '0');  -- y = 0 (acumulador)
                        z := x"0100";  -- z = 1.0 (para log2(1+x))
                    when "00" =>  -- exp(x)
                        x := (others => '0');  -- x = 0
                        y := x"0100";  -- y = 1.0
                        z := input;  -- z = input
                    when others =>
                        -- sqrt: implementar separadamente
                        x := input;
                        y := (others => '0');
                        z := input;
                end case;

                x_reg <= x;
                y_reg <= y;
                z_reg <= z;

            elsif active = '1' then
                -- Iteração CORDIC
                if iteration < ITERATIONS then
                    x := x_reg;
                    y := y_reg;
                    z := z_reg;

                    case op_reg is
                        when "01" =>  -- log2(1+x): modo vectoring
                            direction := '0' when y < 0 else '1';

                            if direction = '1' then
                                x_next := x + (y shift_right iteration);
                                y_next := y - (x shift_right iteration);
                                z_next := z + ATAN_TABLE(iteration);
                            else
                                x_next := x - (y shift_right iteration);
                                y_next := y + (x shift_right iteration);
                                z_next := z - ATAN_TABLE(iteration);
                            end if;

                        when "00" =>  -- exp(x): modo rotation
                            direction := '0' when z < 0 else '1';

                            if direction = '1' then
                                x_next := x - (y shift_right iteration);
                                y_next := y + (x shift_right iteration);
                                z_next := z - LOG_TABLE(iteration);
                            else
                                x_next := x + (y shift_right iteration);
                                y_next := y - (x shift_right iteration);
                                z_next := z + LOG_TABLE(iteration);
                            end if;

                        when others =>
                            x_next := x;
                            y_next := y;
                            z_next := z;
                    end case;

                    x_reg <= x_next;
                    y_reg <= y_next;
                    z_reg <= z_next;
                    iteration <= iteration + 1;

                else
                    -- Iterações completas: output resultado
                    case op_reg is
                        when "01" => result <= z_reg;  -- log2(1+x)
                        when "00" => result <= y_reg;  -- exp(x)
                        when others => result <= x_reg;  -- sqrt
                    end case;

                    done <= '1';
                    active <= '0';
                    iteration <= 0;
                end if;
            end if;
        end if;
    end process;

end Behavioral;
