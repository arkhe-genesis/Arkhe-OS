use anchor_lang::prelude::*;
use counter::cpi::accounts::Increment;
use counter::program::Counter as CounterProgram;
use counter::{self, Counter};

declare_id!("CpiTester1111111111111111111111111111111111");

#[program]
pub mod cpi_tester {
    use super::*;

    pub fn invoke_increment(ctx: Context<InvokeIncrement>) -> Result<()> {
        let cpi_program = ctx.accounts.counter_program.to_account_info();
        let cpi_accounts = Increment {
            counter: ctx.accounts.counter_account.to_account_info(),
        };
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);

        counter::cpi::increment(cpi_ctx)?;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InvokeIncrement<'info> {
    #[account(mut)]
    pub counter_account: Account<'info, Counter>,
    pub counter_program: Program<'info, CounterProgram>,
}
