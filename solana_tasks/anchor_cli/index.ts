import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const args = process.argv.slice(2);
const projectName = args[0];

if (!projectName) {
    console.error("Please provide a project name.");
    process.exit(1);
}

const targetDir = path.resolve(process.cwd(), projectName);

if (fs.existsSync(targetDir)) {
    console.error(`Directory ${projectName} already exists.`);
    process.exit(1);
}

fs.mkdirSync(targetDir, { recursive: true });

// Scaffolding Cargo.toml
const cargoToml = `[workspace]
members = [
    "programs/*"
]
`;
fs.writeFileSync(path.join(targetDir, 'Cargo.toml'), cargoToml);

// Scaffolding Anchor.toml
const anchorToml = `[toolchain]

[features]
seeds = false
skip-lint = false

[programs.localnet]
${projectName} = "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "Localnet"
wallet = "~/.config/solana/id.json"

[scripts]
test = "yarn run ts-mocha -p ./tsconfig.json -t 1000000 tests/**/*.ts"
`;
fs.writeFileSync(path.join(targetDir, 'Anchor.toml'), anchorToml);

// Scaffolding program directory
const programsDir = path.join(targetDir, 'programs', projectName);
fs.mkdirSync(path.join(programsDir, 'src'), { recursive: true });

const programCargoToml = `[package]
name = "${projectName}"
version = "0.1.0"
edition = "2021"

[dependencies]
anchor-lang = "0.30.1"

[lib]
crate-type = ["cdylib", "lib"]
`;
fs.writeFileSync(path.join(programsDir, 'Cargo.toml'), programCargoToml);

const programLibRs = `use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod ${projectName.replace(/-/g, '_')} {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}
`;
fs.writeFileSync(path.join(programsDir, 'src', 'lib.rs'), programLibRs);

console.log(`Scaffolded Anchor project in ${targetDir}`);
