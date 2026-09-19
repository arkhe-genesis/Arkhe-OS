# Arkhe OS agent instructions

This is a polyglot monorepository.  Do not infer a repository-wide runtime,
package manager, or test command from the directory in which you start.

## Start here

Read [`docs/architecture/AI_AGENT_OPERATING_MODEL.md`](docs/architecture/AI_AGENT_OPERATING_MODEL.md)
before changing code.  It identifies the maintained workspace, adjacent
standalone projects, trust boundaries, and validation rules.

## Working agreement

1. Scope a change to one deployable or one workspace member unless the task
   explicitly crosses a boundary.
2. Read the closest `README`, manifest, and any nested `AGENTS.md` before
   editing that component.
3. Treat keys, signatures, identity, governance, cryptography, boot/kernel,
   hardware, and deployment code as security-sensitive. Preserve wire formats
   and public APIs unless the task explicitly calls for a migration.
4. Never edit generated files, vendored dependencies, binary artifacts, or
   local build state as part of a source change.
5. Run the narrowest relevant checks first; report commands that could not run
   and why. Do not claim that the entire repository was built unless it was.

## Source of truth

The shared operating model is intentionally tool-neutral. Tool-specific entry
points in `.agents`, `.agi`, `.claude`, `.clinerules`, `.cursor`, and `.github`
link to it instead of maintaining competing architecture descriptions.
