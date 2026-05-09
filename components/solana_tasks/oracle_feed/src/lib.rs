use anchor_lang::prelude::*;
use std::convert::TryInto;

declare_id!("OracleFeed1111111111111111111111111111111111");

// A simplified mock of a Pyth price feed account structure for compilation
#[account]
pub struct MockPythPriceAccount {
    pub magic: u32,
    pub version: u32,
    pub price: i64,
    pub conf: u64,
    pub expo: i32,
}

#[program]
pub mod oracle_feed {
    use super::*;

    pub fn read_price(ctx: Context<ReadPrice>) -> Result<()> {
        let price_account_info = &ctx.accounts.pyth_account;

        // Ensure the account belongs to Pyth (simplified mock logic)
        // In reality, you'd use a Pyth SDK or deserialize properly
        let data = price_account_info.try_borrow_data()?;

        // Mock check (e.g., magic number)
        if data.len() < 8 {
             return err!(ErrorCode::InvalidOracleData);
        }

        msg!("Read raw data from oracle");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ReadPrice<'info> {
    /// CHECK: We are mocking the Pyth price account read
    pub pyth_account: UncheckedAccount<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid Oracle Data")]
    InvalidOracleData,
}
