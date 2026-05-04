use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

declare_id!("StakeVauLt111111111111111111111111111111111");

#[program]
pub mod staking_vault {
    use super::*;

    pub fn initialize_stake(ctx: Context<InitializeStake>, lock_duration: i64) -> Result<()> {
        let stake_state = &mut ctx.accounts.stake_state;
        stake_state.owner = ctx.accounts.user.key();
        stake_state.unlock_time = Clock::get()?.unix_timestamp + lock_duration;
        stake_state.amount = 0;
        stake_state.bump = ctx.bumps.stake_state;
        Ok(())
    }

    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let cpi_accounts = Transfer {
            from: ctx.accounts.user_token_account.to_account_info(),
            to: ctx.accounts.vault_token_account.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);

        token::transfer(cpi_ctx, amount)?;

        let stake_state = &mut ctx.accounts.stake_state;
        stake_state.amount += amount;

        Ok(())
    }

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        let stake_state = &mut ctx.accounts.stake_state;

        require!(Clock::get()?.unix_timestamp >= stake_state.unlock_time, ErrorCode::TokensLocked);
        require!(stake_state.amount >= amount, ErrorCode::InsufficientFunds);

        let bump = stake_state.bump;
        let owner = stake_state.owner;
        let signer_seeds: &[&[&[u8]]] = &[&[
            b"stake",
            owner.as_ref(),
            &[bump],
        ]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.vault_token_account.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: stake_state.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer_seeds);

        token::transfer(cpi_ctx, amount)?;

        stake_state.amount -= amount;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeStake<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 8 + 1,
        seeds = [b"stake", user.key().as_ref()],
        bump
    )]
    pub stake_state: Account<'info, StakeState>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        mut,
        seeds = [b"stake", user.key().as_ref()],
        bump = stake_state.bump,
        has_one = owner @ ErrorCode::InvalidOwner
    )]
    pub stake_state: Account<'info, StakeState>,
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub vault_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(
        mut,
        seeds = [b"stake", user.key().as_ref()],
        bump = stake_state.bump,
        has_one = owner @ ErrorCode::InvalidOwner
    )]
    pub stake_state: Account<'info, StakeState>,
    #[account(mut)]
    pub vault_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct StakeState {
    pub owner: Pubkey,
    pub unlock_time: i64,
    pub amount: u64,
    pub bump: u8,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Tokens are still locked.")]
    TokensLocked,
    #[msg("Insufficient funds to withdraw.")]
    InsufficientFunds,
    #[msg("Invalid owner.")]
    InvalidOwner,
}
