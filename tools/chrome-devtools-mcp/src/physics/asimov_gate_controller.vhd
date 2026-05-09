-- asimov_gate_controller.vhd
-- Arkhe(n) Asimov Gate Physical Cutoff Controller - VHDL

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity asimov_gate_controller is
    Port (
        clk             : in  STD_LOGIC;
        reset           : in  STD_LOGIC;
        crs_in          : in  STD_LOGIC_VECTOR(31 downto 0); -- Q16.16 Fixed Point
        threshold       : in  STD_LOGIC_VECTOR(31 downto 0); -- Q16.16 Fixed Point
        alarm_trigger   : in  STD_LOGIC;
        phaser_enable   : out STD_LOGIC;
        status_reg      : out STD_LOGIC_VECTOR(31 downto 0)
    );
end asimov_gate_controller;

architecture Behavioral of asimov_gate_controller is
    constant CRS_BLOCK_LIMIT : unsigned(31 downto 0) := x"0000CCCC"; -- 0.80 in Q16.16
    signal internal_veto : STD_LOGIC := '0';
begin

    process(clk, reset)
    begin
        if reset = '1' then
            phaser_enable <= '1';
            internal_veto <= '0';
            status_reg <= (others => '0');
        elsif rising_edge(clk) then
            -- 1. Check for physical alarm or severe decoherence
            if alarm_trigger = '1' or unsigned(crs_in) < CRS_BLOCK_LIMIT then
                phaser_enable <= '0'; -- PHYSICAL CUTOFF
                internal_veto <= '1';
                status_reg(0) <= '1'; -- Veto bit
            -- 2. Check for threshold-based warning
            elsif unsigned(crs_in) < unsigned(threshold) then
                phaser_enable <= '1';
                status_reg(1) <= '1'; -- Phase correction needed bit
            else
                phaser_enable <= '1';
                status_reg <= (others => '0');
            end if;
        end if;
    end process;

end Behavioral;
