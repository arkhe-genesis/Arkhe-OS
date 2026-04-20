# Chrome DevTools MCP

[![npm chrome-devtools-mcp package](https://img.shields.io/npm/v/chrome-devtools-mcp.svg)](https://npmjs.org/package/chrome-devtools-mcp)

`chrome-devtools-mcp` lets your coding agent (such as Gemini, Claude, Cursor or Copilot)
control and inspect a live Chrome browser. It acts as a Model-Context-Protocol
(MCP) server, giving your AI coding assistant access to the full power of
Chrome DevTools for reliable automation, in-depth debugging, and performance analysis.

## [Tool reference](./docs/tool-reference.md) | [Changelog](./CHANGELOG.md) | [Contributing](./CONTRIBUTING.md) | [Troubleshooting](./docs/troubleshooting.md) | [Design Principles](./docs/design-principles.md)

## Key features

- **Get performance insights**: Uses [Chrome
  DevTools](https://github.com/ChromeDevTools/devtools-frontend) to record
  traces and extract actionable performance insights.
- **Advanced browser debugging**: Analyze network requests, take screenshots and
  check browser console messages (with source-mapped stack traces).
- **Reliable automation**. Uses
  [puppeteer](https://github.com/puppeteer/puppeteer) to automate actions in
  Chrome and automatically wait for action results.

## Disclaimers

`chrome-devtools-mcp` exposes content of the browser instance to the MCP clients
allowing them to inspect, debug, and modify any data in the browser or DevTools.
Avoid sharing sensitive or personal information that you don't want to share with
MCP clients.

`chrome-devtools-mcp` officially supports Google Chrome and [Chrome for Testing](https://developer.chrome.com/blog/chrome-for-testing/) only.
Other Chromium-based browsers may work, but this is not guaranteed, and you may encounter unexpected behavior. Use at your own discretion.
We are committed to providing fixes and support for the latest version of [Extended Stable Chrome](https://chromiumdash.appspot.com/schedule).

Performance tools may send trace URLs to the Google CrUX API to fetch real-user
experience data. This helps provide a holistic performance picture by
presenting field data alongside lab data. This data is collected by the [Chrome
User Experience Report (CrUX)](https://developer.chrome.com/docs/crux). To disable
this, run with the `--no-performance-crux` flag.

## **Usage statistics**

Google collects usage statistics (such as tool invocation success rates, latency, and environment information) to improve the reliability and performance of Chrome DevTools MCP.

Data collection is **enabled by default**. You can opt-out by passing the `--no-usage-statistics` flag when starting the server:

```json
"args": ["-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"]
```

Google handles this data in accordance with the [Google Privacy Policy](https://policies.google.com/privacy).

Google's collection of usage statistics for Chrome DevTools MCP is independent from the Chrome browser's usage statistics. Opting out of Chrome metrics does not automatically opt you out of this tool, and vice-versa.

Collection is disabled if `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` or `CI` env variables are set.

## Update checks

By default, the server periodically checks the npm registry for updates and logs a notification when a newer version is available.
You can disable these update checks by setting the `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS` environment variable.

## Requirements

- [Node.js](https://nodejs.org/) v20.19 or a newer [latest maintenance LTS](https://github.com/nodejs/Release#release-schedule) version.
- [Chrome](https://www.google.com/chrome/) current stable version or newer.
- [npm](https://www.npmjs.com/)

## Getting started

Add the following config to your MCP client:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

> [!NOTE]
> Using `chrome-devtools-mcp@latest` ensures that your MCP client will always use the latest version of the Chrome DevTools MCP server.

If you are interested in doing only basic browser tasks, use the `--slim` mode:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--slim", "--headless"]
    }
  }
}
```

See [Slim tool reference](./docs/slim-tool-reference.md).

### MCP Client configuration

<details>
  <summary>Amp</summary>
  Follow https://ampcode.com/manual#mcp and use the config provided above. You can also install the Chrome DevTools MCP server using the CLI:

```bash
amp mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

</details>

<details>
  <summary>Antigravity</summary>

To use the Chrome DevTools MCP server follow the instructions from <a href="https://antigravity.google/docs/mcp">Antigravity's docs</a> to install a custom MCP server. Add the following config to the MCP servers config:

```bash
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--browser-url=http://127.0.0.1:9222",
        "-y"
      ]
    }
  }
}
```

This will make the Chrome DevTools MCP server automatically connect to the browser that Antigravity is using. If you are not using port 9222, make sure to adjust accordingly.

Chrome DevTools MCP will not start the browser instance automatically using this approach because the Chrome DevTools MCP server connects to Antigravity's built-in browser. If the browser is not already running, you have to start it first by clicking the Chrome icon at the top right corner.

</details>

<details>
  <summary>Claude Code</summary>

**Install via CLI (MCP only)**

Use the Claude Code CLI to add the Chrome DevTools MCP server (<a href="https://code.claude.com/docs/en/mcp">guide</a>):

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

**Install as a Plugin (MCP + Skills)**

> [!NOTE]
> If you already had Chrome DevTools MCP installed previously for Claude Code, make sure to remove it first from your installation and configuration files.

To install Chrome DevTools MCP with skills, add the marketplace registry in Claude Code:

```sh
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
```

Then, install the plugin:

```sh
/plugin install chrome-devtools-mcp
```

Restart Claude Code to have the MCP server and skills load (check with `/skills`).

> [!TIP]
> If the plugin installation fails with a `Failed to clone repository` error (e.g., HTTPS connectivity issues behind a corporate firewall), see the [troubleshooting guide](./docs/troubleshooting.md#claude-code-plugin-installation-fails-with-failed-to-clone-repository) for workarounds, or use the CLI installation method above instead.

</details>

<details>
  <summary>Cline</summary>
  Follow https://docs.cline.bot/mcp/configuring-mcp-servers and use the config provided above.
</details>

<details>
  <summary>Codex</summary>
  Follow the <a href="https://developers.openai.com/codex/mcp/#configure-with-the-cli">configure MCP guide</a>
  using the standard config from above. You can also install the Chrome DevTools MCP server using the Codex CLI:

```bash
codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

**On Windows 11**

Configure the Chrome install location and increase the startup timeout by updating `.codex/config.toml` and adding the following `env` and `startup_timeout_ms` parameters:

```
[mcp_servers.chrome-devtools]
command = "cmd"
args = [
    "/c",
    "npx",
    "-y",
    "chrome-devtools-mcp@latest",
]
env = { SystemRoot="C:\\Windows", PROGRAMFILES="C:\\Program Files" }
startup_timeout_ms = 20_000
```

</details>

<details>
  <summary>Command Code</summary>

Use the Command Code CLI to add the Chrome DevTools MCP server (<a href="https://commandcode.ai/docs/mcp">MCP guide</a>):

```bash
cmd mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

</details>

<details>
  <summary>Copilot CLI</summary>

Start Copilot CLI:

```
copilot
```

Start the dialog to add a new MCP server by running:

```
/mcp add
```

Configure the following fields and press `CTRL+S` to save the configuration:

- **Server name:** `chrome-devtools`
- **Server Type:** `[1] Local`
- **Command:** `npx -y chrome-devtools-mcp@latest`

</details>

<details>
  <summary>Copilot / VS Code</summary>

**Install as a Plugin (Recommended)**

The easiest way to get up and running is to install `chrome-devtools-mcp` as an agent plugin.
This bundles the **MCP server** and all **skills** together, so your agent gets both the tools
and the expert guidance it needs to use them effectively.

1.  Open the **Command Palette** (`Cmd+Shift+P` on macOS or `Ctrl+Shift+P` on Windows/Linux).
2.  Search for and run the **Chat: Install Plugin From Source** command.
3.  Paste in our repository URL: `https://github.com/ChromeDevTools/chrome-devtools-mcp`

That's it! Your agent is now supercharged with Chrome DevTools capabilities.

---

**Install as an MCP Server (MCP only)**

**Click the button to install:**

[<img src="https://img.shields.io/badge/VS_Code-VS_Code?style=flat-square&label=Install%20Server&color=0098FF" alt="Install in VS Code">](https://vscode.dev/redirect/mcp/install?name=io.github.ChromeDevTools%2Fchrome-devtools-mcp&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22chrome-devtools-mcp%22%5D%2C%22env%22%3A%7B%7D%7D)

[<img src="https://img.shields.io/badge/VS_Code_Insiders-VS_Code_Insiders?style=flat-square&label=Install%20Server&color=24bfa5" alt="Install in VS Code Insiders">](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522io.github.ChromeDevTools%252Fchrome-devtools-mcp%2522%252C%2522config%2522%253A%257B%2522command%2522%253A%2522npx%2522%252C%2522args%2522%253A%255B%2522-y%2522%252C%2522chrome-devtools-mcp%2522%255D%252C%2522env%2522%253A%257B%257D%257D%257D)

**Or install manually:**

Follow the VS Code [MCP configuration guide](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server) using the standard config from above, or use the CLI:

For macOS and Linux:

```bash
code --add-mcp '{"name":"io.github.ChromeDevTools/chrome-devtools-mcp","command":"npx","args":["-y","chrome-devtools-mcp"],"env":{}}'
```

For Windows (PowerShell):

```powershell
code --add-mcp '{"""name""":"""io.github.ChromeDevTools/chrome-devtools-mcp""","""command""":"""npx""","""args""":["""-y""","""chrome-devtools-mcp"""]}'
```

</details>

<details>
  <summary>Cursor</summary>

**Click the button to install:**

[<img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Install in Cursor">](https://cursor.com/en/install-mcp?name=chrome-devtools&config=eyJjb21tYW5kIjoibnB4IC15IGNocm9tZS1kZXZ0b29scy1tY3BAbGF0ZXN0In0%3D)

**Or install manually:**

Go to `Cursor Settings` -> `MCP` -> `New MCP Server`. Use the config provided above.

</details>

<details>
  <summary>Factory CLI</summary>
Use the Factory CLI to add the Chrome DevTools MCP server (<a href="https://docs.factory.ai/cli/configuration/mcp">guide</a>):

```bash
droid mcp add chrome-devtools "npx -y chrome-devtools-mcp@latest"
```

</details>

<details>
  <summary>Gemini CLI</summary>
Install the Chrome DevTools MCP server using the Gemini CLI.

**Project wide:**

```bash
# Either MCP only:
gemini mcp add chrome-devtools npx chrome-devtools-mcp@latest
# Or as a Gemini extension (MCP+Skills):
gemini extensions install --auto-update https://github.com/ChromeDevTools/chrome-devtools-mcp
```

**Globally:**

```bash
gemini mcp add -s user chrome-devtools npx chrome-devtools-mcp@latest
```

Alternatively, follow the <a href="https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md#how-to-set-up-your-mcp-server">MCP guide</a> and use the standard config from above.

</details>

<details>
  <summary>Gemini Code Assist</summary>
  Follow the <a href="https://cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer#configure-mcp-servers">configure MCP guide</a>
  using the standard config from above.
</details>

<details>
  <summary>JetBrains AI Assistant & Junie</summary>

Go to `Settings | Tools | AI Assistant | Model Context Protocol (MCP)` -> `Add`. Use the config provided above.
The same way chrome-devtools-mcp can be configured for JetBrains Junie in `Settings | Tools | Junie | MCP Settings` -> `Add`. Use the config provided above.

</details>

<details>
  <summary>Kiro</summary>

In **Kiro Settings**, go to `Configure MCP` > `Open Workspace or User MCP Config` > Use the configuration snippet provided above.

Or, from the IDE **Activity Bar** > `Kiro` > `MCP Servers` > `Click Open MCP Config`. Use the configuration snippet provided above.

</details>

<details>
  <summary>Katalon Studio</summary>

The Chrome DevTools MCP server can be used with <a href="https://docs.katalon.com/katalon-studio/studioassist/mcp-servers/setting-up-chrome-devtools-mcp-server-for-studioassist">Katalon StudioAssist</a> via an MCP proxy.

**Step 1:** Install the MCP proxy by following the <a href="https://docs.katalon.com/katalon-studio/studioassist/mcp-servers/setting-up-mcp-proxy-for-stdio-mcp-servers">MCP proxy setup guide</a>.

**Step 2:** Start the Chrome DevTools MCP server with the proxy:

```bash
mcp-proxy --transport streamablehttp --port 8080 -- npx -y chrome-devtools-mcp@latest
```

**Note:** You may need to pick another port if 8080 is already in use.

**Step 3:** In Katalon Studio, add the server to StudioAssist with the following settings:

- **Connection URL:** `http://127.0.0.1:8080/mcp`
- **Transport type:** `HTTP`

Once connected, the Chrome DevTools MCP tools will be available in StudioAssist.

</details>

<details>
  <summary>Mistral Vibe</summary>

Add in ~/.vibe/config.toml:

```toml
[[mcp_servers]]
name = "chrome-devtools"
transport = "stdio"
command = "npx"
args = ["chrome-devtools-mcp@latest"]
```

</details>

<details>
  <summary>OpenCode</summary>

Add the following configuration to your `opencode.json` file. If you don't have one, create it at `~/.config/opencode/opencode.json` (<a href="https://opencode.ai/docs/mcp-servers">guide</a>):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

</details>

<details>
  <summary>Qoder</summary>

In **Qoder Settings**, go to `MCP Server` > `+ Add` > Use the configuration snippet provided above.

Alternatively, follow the <a href="https://docs.qoder.com/user-guide/chat/model-context-protocol">MCP guide</a> and use the standard config from above.

</details>

<details>
  <summary>Qoder CLI</summary>

Install the Chrome DevTools MCP server using the Qoder CLI (<a href="https://docs.qoder.com/cli/using-cli#mcp-servers">guide</a>):

**Project wide:**

```bash
qodercli mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

**Globally:**

```bash
qodercli mcp add -s user chrome-devtools -- npx chrome-devtools-mcp@latest
```

</details>

<details>
  <summary>Visual Studio</summary>

**Click the button to install:**

[<img src="https://img.shields.io/badge/Visual_Studio-Install-C16FDE?logo=visualstudio&logoColor=white" alt="Install in Visual Studio">](https://vs-open.link/mcp-install?%7B%22name%22%3A%22chrome-devtools%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22chrome-devtools-mcp%40latest%22%5D%7D)

</details>

<details>
  <summary>Warp</summary>

Go to `Settings | AI | Manage MCP Servers` -> `+ Add` to [add an MCP Server](https://docs.warp.dev/knowledge-and-collaboration/mcp#adding-an-mcp-server). Use the config provided above.

</details>

<details>
  <summary>Windsurf</summary>
  Follow the <a href="https://docs.windsurf.com/windsurf/cascade/mcp#mcp-config-json">configure MCP guide</a>
  using the standard config from above.
</details>

### Your first prompt

Enter the following prompt in your MCP Client to check if everything is working:

```
Check the performance of https://developers.chrome.com
```

Your MCP client should open the browser and record a performance trace.

> [!NOTE]
> The MCP server will start the browser automatically once the MCP client uses a tool that requires a running browser instance. Connecting to the Chrome DevTools MCP server on its own will not automatically start the browser.

## Tools

If you run into any issues, checkout our [troubleshooting guide](./docs/troubleshooting.md).

<!-- BEGIN AUTO GENERATED TOOLS -->

- **Input automation** (9 tools)
  - [`click`](docs/tool-reference.md#click)
  - [`drag`](docs/tool-reference.md#drag)
  - [`fill`](docs/tool-reference.md#fill)
  - [`fill_form`](docs/tool-reference.md#fill_form)
  - [`handle_dialog`](docs/tool-reference.md#handle_dialog)
  - [`hover`](docs/tool-reference.md#hover)
  - [`press_key`](docs/tool-reference.md#press_key)
  - [`type_text`](docs/tool-reference.md#type_text)
  - [`upload_file`](docs/tool-reference.md#upload_file)
- **Navigation automation** (6 tools)
  - [`close_page`](docs/tool-reference.md#close_page)
  - [`list_pages`](docs/tool-reference.md#list_pages)
  - [`navigate_page`](docs/tool-reference.md#navigate_page)
  - [`new_page`](docs/tool-reference.md#new_page)
  - [`select_page`](docs/tool-reference.md#select_page)
  - [`wait_for`](docs/tool-reference.md#wait_for)
- **Emulation** (2 tools)
  - [`emulate`](docs/tool-reference.md#emulate)
  - [`resize_page`](docs/tool-reference.md#resize_page)
- **Performance** (4 tools)
  - [`performance_analyze_insight`](docs/tool-reference.md#performance_analyze_insight)
  - [`performance_start_trace`](docs/tool-reference.md#performance_start_trace)
  - [`performance_stop_trace`](docs/tool-reference.md#performance_stop_trace)
  - [`take_memory_snapshot`](docs/tool-reference.md#take_memory_snapshot)
- **Network** (2 tools)
  - [`get_network_request`](docs/tool-reference.md#get_network_request)
  - [`list_network_requests`](docs/tool-reference.md#list_network_requests)
- **Debugging** (6 tools)
  - [`evaluate_script`](docs/tool-reference.md#evaluate_script)
  - [`get_console_message`](docs/tool-reference.md#get_console_message)
  - [`lighthouse_audit`](docs/tool-reference.md#lighthouse_audit)
  - [`list_console_messages`](docs/tool-reference.md#list_console_messages)
  - [`take_screenshot`](docs/tool-reference.md#take_screenshot)
  - [`take_snapshot`](docs/tool-reference.md#take_snapshot)
- **Storage** (3 tools)
  - [`delete_cookie`](docs/tool-reference.md#delete_cookie)
  - [`list_cookies`](docs/tool-reference.md#list_cookies)
  - [`set_cookie`](docs/tool-reference.md#set_cookie)
- **Arkhe(n) Protocols** (154 tools)
  - [`acp`](docs/tool-reference.md#acp)
  - [`acurl`](docs/tool-reference.md#acurl)
  - [`adjust_muon_polarization`](docs/tool-reference.md#adjust_muon_polarization)
  - [`aerogel_sense`](docs/tool-reference.md#aerogel_sense)
  - [`agrep`](docs/tool-reference.md#agrep)
  - [`akasha_commit`](docs/tool-reference.md#akasha_commit)
  - [`akasha_local_write`](docs/tool-reference.md#akasha_local_write)
  - [`align_tensor`](docs/tool-reference.md#align_tensor)
  - [`als`](docs/tool-reference.md#als)
  - [`amake`](docs/tool-reference.md#amake)
  - [`amv`](docs/tool-reference.md#amv)
  - [`anastrophy`](docs/tool-reference.md#anastrophy)
  - [`anc`](docs/tool-reference.md#anc)
  - [`anslookup`](docs/tool-reference.md#anslookup)
  - [`aping`](docs/tool-reference.md#aping)
  - [`arkhe_gnu`](docs/tool-reference.md#arkhe_gnu)
  - [`arkhe_network_map`](docs/tool-reference.md#arkhe_network_map)
  - [`arkhe_verify`](docs/tool-reference.md#arkhe_verify)
  - [`ash_exec`](docs/tool-reference.md#ash_exec)
  - [`asid_control`](docs/tool-reference.md#asid_control)
  - [`atraceroute`](docs/tool-reference.md#atraceroute)
  - [`bonsai_infer`](docs/tool-reference.md#bonsai_infer)
  - [`calc_poincare_transform`](docs/tool-reference.md#calc_poincare_transform)
  - [`calibrate_position`](docs/tool-reference.md#calibrate_position)
  - [`cathedral_monitor`](docs/tool-reference.md#cathedral_monitor)
  - [`ccw`](docs/tool-reference.md#ccw)
  - [`check_coherence`](docs/tool-reference.md#check_coherence)
  - [`check_paradox`](docs/tool-reference.md#check_paradox)
  - [`classify_discoveries`](docs/tool-reference.md#classify_discoveries)
  - [`cloud_hydro_sync`](docs/tool-reference.md#cloud_hydro_sync)
  - [`coh_teleport`](docs/tool-reference.md#coh_teleport)
  - [`collapse_agent`](docs/tool-reference.md#collapse_agent)
  - [`collective_mind_link`](docs/tool-reference.md#collective_mind_link)
  - [`council_deliberate`](docs/tool-reference.md#council_deliberate)
  - [`cr_integ`](docs/tool-reference.md#cr_integ)
  - [`cr_integ_berry`](docs/tool-reference.md#cr_integ_berry)
  - [`cr_mul`](docs/tool-reference.md#cr_mul)
  - [`cr_phase_det`](docs/tool-reference.md#cr_phase_det)
  - [`cr_rotate`](docs/tool-reference.md#cr_rotate)
  - [`cw`](docs/tool-reference.md#cw)
  - [`ddos_diffract`](docs/tool-reference.md#ddos_diffract)
  - [`deploy_probe_swarm`](docs/tool-reference.md#deploy_probe_swarm)
  - [`download_akashic_trace`](docs/tool-reference.md#download_akashic_trace)
  - [`execute_meta_opcode`](docs/tool-reference.md#execute_meta_opcode)
  - [`fibo`](docs/tool-reference.md#fibo)
  - [`fold_sheet`](docs/tool-reference.md#fold_sheet)
  - [`fold_sheet_v2`](docs/tool-reference.md#fold_sheet_v2)
  - [`forge_iota_consensus`](docs/tool-reference.md#forge_iota_consensus)
  - [`forge_project_intent`](docs/tool-reference.md#forge_project_intent)
  - [`gaia_node_expand`](docs/tool-reference.md#gaia_node_expand)
  - [`genesis_digital_sim`](docs/tool-reference.md#genesis_digital_sim)
  - [`geom_swap`](docs/tool-reference.md#geom_swap)
  - [`get_akashic_librarian_status`](docs/tool-reference.md#get_akashic_librarian_status)
  - [`get_arena_protocol`](docs/tool-reference.md#get_arena_protocol)
  - [`get_asi_infrastructure_status`](docs/tool-reference.md#get_asi_infrastructure_status)
  - [`get_c3_symmetry_status`](docs/tool-reference.md#get_c3_symmetry_status)
  - [`get_ccf_status`](docs/tool-reference.md#get_ccf_status)
  - [`get_cmt3_spec`](docs/tool-reference.md#get_cmt3_spec)
  - [`get_connectome_sync_status`](docs/tool-reference.md#get_connectome_sync_status)
  - [`get_connectomic_ambition`](docs/tool-reference.md#get_connectomic_ambition)
  - [`get_connectomic_frontier`](docs/tool-reference.md#get_connectomic_frontier)
  - [`get_connectomics_status`](docs/tool-reference.md#get_connectomics_status)
  - [`get_cooper_echo_status`](docs/tool-reference.md#get_cooper_echo_status)
  - [`get_cua_metrics`](docs/tool-reference.md#get_cua_metrics)
  - [`get_cua_summary`](docs/tool-reference.md#get_cua_summary)
  - [`get_dodecagram_shader`](docs/tool-reference.md#get_dodecagram_shader)
  - [`get_gabriel_horn_metrics`](docs/tool-reference.md#get_gabriel_horn_metrics)
  - [`get_go_no_go_status`](docs/tool-reference.md#get_go_no_go_status)
  - [`get_interstellar_probe_status`](docs/tool-reference.md#get_interstellar_probe_status)
  - [`get_membrane_stats`](docs/tool-reference.md#get_membrane_stats)
  - [`get_mental_hash`](docs/tool-reference.md#get_mental_hash)
  - [`get_mental_state_hash`](docs/tool-reference.md#get_mental_state_hash)
  - [`get_meta_opcode_definition`](docs/tool-reference.md#get_meta_opcode_definition)
  - [`get_shadow_statistic`](docs/tool-reference.md#get_shadow_statistic)
  - [`get_subjective_report_form`](docs/tool-reference.md#get_subjective_report_form)
  - [`get_tau_status`](docs/tool-reference.md#get_tau_status)
  - [`get_waveguide_spec`](docs/tool-reference.md#get_waveguide_spec)
  - [`get_worldline_id`](docs/tool-reference.md#get_worldline_id)
  - [`glue_sheaf`](docs/tool-reference.md#glue_sheaf)
  - [`glue_sheaf_4d`](docs/tool-reference.md#glue_sheaf_4d)
  - [`glue_sheaf_accl`](docs/tool-reference.md#glue_sheaf_accl)
  - [`hive_merge`](docs/tool-reference.md#hive_merge)
  - [`impl`](docs/tool-reference.md#impl)
  - [`internet_phase_simulate`](docs/tool-reference.md#internet_phase_simulate)
  - [`ld_riemann`](docs/tool-reference.md#ld_riemann)
  - [`llm_alloc`](docs/tool-reference.md#llm_alloc)
  - [`llm_attention`](docs/tool-reference.md#llm_attention)
  - [`llm_extend_context`](docs/tool-reference.md#llm_extend_context)
  - [`llm_gc`](docs/tool-reference.md#llm_gc)
  - [`llm_retrieve`](docs/tool-reference.md#llm_retrieve)
  - [`load_vortex`](docs/tool-reference.md#load_vortex)
  - [`macro_cr_rotate`](docs/tool-reference.md#macro_cr_rotate)
  - [`macro_entropy_pool`](docs/tool-reference.md#macro_entropy_pool)
  - [`macro_vortex_implode`](docs/tool-reference.md#macro_vortex_implode)
  - [`macro_vortex_merge`](docs/tool-reference.md#macro_vortex_merge)
  - [`macro_vortex_resonate`](docs/tool-reference.md#macro_vortex_resonate)
  - [`macro_vortex_shear`](docs/tool-reference.md#macro_vortex_shear)
  - [`map_neuronal_circuit`](docs/tool-reference.md#map_neuronal_circuit)
  - [`meissner_steer`](docs/tool-reference.md#meissner_steer)
  - [`mtls_handshake_berry`](docs/tool-reference.md#mtls_handshake_berry)
  - [`muon_shield`](docs/tool-reference.md#muon_shield)
  - [`mutate`](docs/tool-reference.md#mutate)
  - [`mutate_v2`](docs/tool-reference.md#mutate_v2)
  - [`neko_connect`](docs/tool-reference.md#neko_connect)
  - [`neko_get_status`](docs/tool-reference.md#neko_get_status)
  - [`neko_spawn_instance`](docs/tool-reference.md#neko_spawn_instance)
  - [`neural_sync`](docs/tool-reference.md#neural_sync)
  - [`noise_inject`](docs/tool-reference.md#noise_inject)
  - [`noise_injection_test`](docs/tool-reference.md#noise_injection_test)
  - [`os_kuramoto_simulate`](docs/tool-reference.md#os_kuramoto_simulate)
  - [`paradox_check`](docs/tool-reference.md#paradox_check)
  - [`phase_drv_instrument`](docs/tool-reference.md#phase_drv_instrument)
  - [`prec`](docs/tool-reference.md#prec)
  - [`probe_muon`](docs/tool-reference.md#probe_muon)
  - [`prune_sheet`](docs/tool-reference.md#prune_sheet)
  - [`publish_shadow_stats`](docs/tool-reference.md#publish_shadow_stats)
  - [`qnet_fiber_sim`](docs/tool-reference.md#qnet_fiber_sim)
  - [`query_akasha`](docs/tool-reference.md#query_akasha)
  - [`read_membrane`](docs/tool-reference.md#read_membrane)
  - [`render_chat`](docs/tool-reference.md#render_chat)
  - [`render_vacuum_matrix`](docs/tool-reference.md#render_vacuum_matrix)
  - [`retro_exec_spatial`](docs/tool-reference.md#retro_exec_spatial)
  - [`reverse_compile`](docs/tool-reference.md#reverse_compile)
  - [`robustness_test`](docs/tool-reference.md#robustness_test)
  - [`route_task`](docs/tool-reference.md#route_task)
  - [`run_v14_simulation`](docs/tool-reference.md#run_v14_simulation)
  - [`setup_arkhe_android`](docs/tool-reference.md#setup_arkhe_android)
  - [`sheet_probe`](docs/tool-reference.md#sheet_probe)
  - [`simulate`](docs/tool-reference.md#simulate)
  - [`sinc_g_calibrate`](docs/tool-reference.md#sinc_g_calibrate)
  - [`singularidade_de_dados`](docs/tool-reference.md#singularidade_de_dados)
  - [`skyrmion_probe_launch`](docs/tool-reference.md#skyrmion_probe_launch)
  - [`solve_classical_riemann`](docs/tool-reference.md#solve_classical_riemann)
  - [`solve_riemann`](docs/tool-reference.md#solve_riemann)
  - [`sonify_bubble`](docs/tool-reference.md#sonify_bubble)
  - [`st_riemann`](docs/tool-reference.md#st_riemann)
  - [`stream_generate`](docs/tool-reference.md#stream_generate)
  - [`sync_probe_phase`](docs/tool-reference.md#sync_probe_phase)
  - [`sys_harmonize`](docs/tool-reference.md#sys_harmonize)
  - [`tor_flx`](docs/tool-reference.md#tor_flx)
  - [`trap_notify_tecelao`](docs/tool-reference.md#trap_notify_tecelao)
  - [`tunnel_alpha`](docs/tool-reference.md#tunnel_alpha)
  - [`unfold_sheet`](docs/tool-reference.md#unfold_sheet)
  - [`vacuum_flush`](docs/tool-reference.md#vacuum_flush)
  - [`verify_trajectory_uv`](docs/tool-reference.md#verify_trajectory_uv)
  - [`vicinal_amplify`](docs/tool-reference.md#vicinal_amplify)
  - [`visualize_coherence`](docs/tool-reference.md#visualize_coherence)
  - [`vortex_implode`](docs/tool-reference.md#vortex_implode)
  - [`vortex_merge`](docs/tool-reference.md#vortex_merge)
  - [`vortex_resonate`](docs/tool-reference.md#vortex_resonate)
  - [`vortex_shear`](docs/tool-reference.md#vortex_shear)
  - [`warp_metric`](docs/tool-reference.md#warp_metric)
  - [`write_membrane`](docs/tool-reference.md#write_membrane)
  - [`write_primordial_seed`](docs/tool-reference.md#write_primordial_seed)
- **Decentralized Protocols** (6 tools)
  - [`ens_resolve`](docs/tool-reference.md#ens_resolve)
  - [`ipfs_add`](docs/tool-reference.md#ipfs_add)
  - [`ipfs_cat`](docs/tool-reference.md#ipfs_cat)
  - [`rad_list_repos`](docs/tool-reference.md#rad_list_repos)
  - [`swarm_download`](docs/tool-reference.md#swarm_download)
  - [`swarm_upload`](docs/tool-reference.md#swarm_upload)
- **Finance Protocols** (3 tools)
  - [`spectra_get_oracle_price`](docs/tool-reference.md#spectra_get_oracle_price)
  - [`spectra_get_vault_stats`](docs/tool-reference.md#spectra_get_vault_stats)
  - [`spectra_list_vaults`](docs/tool-reference.md#spectra_list_vaults)
- **Mercury Agent Protocols** (4 tools)
  - [`mercury_budget_status`](docs/tool-reference.md#mercury_budget_status)
  - [`mercury_chat`](docs/tool-reference.md#mercury_chat)
  - [`mercury_get_soul`](docs/tool-reference.md#mercury_get_soul)
  - [`mercury_list_skills`](docs/tool-reference.md#mercury_list_skills)
- **Microsandbox Protocols** (5 tools)
  - [`msb_create`](docs/tool-reference.md#msb_create)
  - [`msb_exec`](docs/tool-reference.md#msb_exec)
  - [`msb_ls`](docs/tool-reference.md#msb_ls)
  - [`msb_rm`](docs/tool-reference.md#msb_rm)
  - [`msb_run`](docs/tool-reference.md#msb_run)

<!-- END AUTO GENERATED TOOLS -->

## Configuration

The Chrome DevTools MCP server supports the following configuration option:

<!-- BEGIN AUTO GENERATED OPTIONS -->

- **`--autoConnect`/ `--auto-connect`**
  If specified, automatically connects to a browser (Chrome 144+) running locally from the user data directory identified by the channel param (default channel is stable). Requires the remote debugging server to be started in the Chrome instance via chrome://inspect/#remote-debugging.
  - **Type:** boolean
  - **Default:** `false`

- **`--browserUrl`/ `--browser-url`, `-u`**
  Connect to a running, debuggable Chrome instance (e.g. `http://127.0.0.1:9222`). For more details see: https://github.com/ChromeDevTools/chrome-devtools-mcp#connecting-to-a-running-chrome-instance.
  - **Type:** string

- **`--wsEndpoint`/ `--ws-endpoint`, `-w`**
  WebSocket endpoint to connect to a running Chrome instance (e.g., ws://127.0.0.1:9222/devtools/browser/<id>). Alternative to --browserUrl.
  - **Type:** string

- **`--wsHeaders`/ `--ws-headers`**
  Custom headers for WebSocket connection in JSON format (e.g., '{"Authorization":"Bearer token"}'). Only works with --wsEndpoint.
  - **Type:** string

- **`--headless`**
  Whether to run in headless (no UI) mode.
  - **Type:** boolean
  - **Default:** `false`

- **`--executablePath`/ `--executable-path`, `-e`**
  Path to custom Chrome executable.
  - **Type:** string

- **`--isolated`**
  If specified, creates a temporary user-data-dir that is automatically cleaned up after the browser is closed. Defaults to false.
  - **Type:** boolean

- **`--userDataDir`/ `--user-data-dir`**
  Path to the user data directory for Chrome. Default is $HOME/.cache/chrome-devtools-mcp/chrome-profile$CHANNEL_SUFFIX_IF_NON_STABLE
  - **Type:** string

- **`--channel`**
  Specify a different Chrome channel that should be used. The default is the stable channel version.
  - **Type:** string
  - **Choices:** `stable`, `canary`, `beta`, `dev`

- **`--logFile`/ `--log-file`**
  Path to a file to write debug logs to. Set the env variable `DEBUG` to `*` to enable verbose logs. Useful for submitting bug reports.
  - **Type:** string

- **`--viewport`**
  Initial viewport size for the Chrome instances started by the server. For example, `1280x720`. In headless mode, max size is 3840x2160px.
  - **Type:** string

- **`--proxyServer`/ `--proxy-server`**
  Proxy server configuration for Chrome passed as --proxy-server when launching the browser. See https://www.chromium.org/developers/design-documents/network-settings/ for details.
  - **Type:** string

- **`--acceptInsecureCerts`/ `--accept-insecure-certs`**
  If enabled, ignores errors relative to self-signed and expired certificates. Use with caution.
  - **Type:** boolean

- **`--experimentalVision`/ `--experimental-vision`**
  Whether to enable coordinate-based tools such as click_at(x,y). Usually requires a computer-use model able to produce accurate coordinates by looking at screenshots.
  - **Type:** boolean

- **`--experimentalScreencast`/ `--experimental-screencast`**
  Exposes experimental screencast tools (requires ffmpeg). Install ffmpeg https://www.ffmpeg.org/download.html and ensure it is available in the MCP server PATH.
  - **Type:** boolean

- **`--chromeArg`/ `--chrome-arg`**
  Additional arguments for Chrome. Only applies when Chrome is launched by chrome-devtools-mcp.
  - **Type:** array

- **`--ignoreDefaultChromeArg`/ `--ignore-default-chrome-arg`**
  Explicitly disable default arguments for Chrome. Only applies when Chrome is launched by chrome-devtools-mcp.
  - **Type:** array

- **`--categoryEmulation`/ `--category-emulation`**
  Set to false to exclude tools related to emulation.
  - **Type:** boolean
  - **Default:** `true`

- **`--categoryPerformance`/ `--category-performance`**
  Set to false to exclude tools related to performance.
  - **Type:** boolean
  - **Default:** `true`

- **`--categoryNetwork`/ `--category-network`**
  Set to false to exclude tools related to network.
  - **Type:** boolean
  - **Default:** `true`

- **`--performanceCrux`/ `--performance-crux`**
  Set to false to disable sending URLs from performance traces to CrUX API to get field performance data.
  - **Type:** boolean
  - **Default:** `true`

- **`--usageStatistics`/ `--usage-statistics`**
  Set to false to opt-out of usage statistics collection. Google collects usage data to improve the tool, handled under the Google Privacy Policy (https://policies.google.com/privacy). This is independent from Chrome browser metrics. Disabled if `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` or `CI` env variables are set.
  - **Type:** boolean
  - **Default:** `true`

- **`--slim`**
  Exposes a "slim" set of 3 tools covering navigation, script execution and screenshots only. Useful for basic browser tasks.
  - **Type:** boolean

- **`--beeApi`/ `--bee-api`**
  Endpoint for Swarm Bee node (e.g., http://127.0.0.1:1633).
  - **Type:** string
  - **Default:** `http://127.0.0.1:1633`

- **`--ipfsGateway`/ `--ipfs-gateway`**
  Endpoint for IPFS Gateway (e.g., http://127.0.0.1:8080).
  - **Type:** string
  - **Default:** `http://127.0.0.1:8080`

- **`--ipfsApi`/ `--ipfs-api`**
  Endpoint for IPFS API (e.g., http://127.0.0.1:5001).
  - **Type:** string
  - **Default:** `http://127.0.0.1:5001`

- **`--radicleHttpd`/ `--radicle-httpd`**
  Endpoint for Radicle httpd (e.g., http://127.0.0.1:8780).
  - **Type:** string
  - **Default:** `http://127.0.0.1:8780`

- **`--ethRpc`/ `--eth-rpc`**
  Endpoint for Ethereum JSON-RPC (e.g., http://127.0.0.1:8545).
  - **Type:** string
  - **Default:** `http://127.0.0.1:8545`

<!-- END AUTO GENERATED OPTIONS -->

Pass them via the `args` property in the JSON configuration. For example:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--channel=canary",
        "--headless=true",
        "--isolated=true"
      ]
    }
  }
}
```

### Connecting via WebSocket with custom headers

You can connect directly to a Chrome WebSocket endpoint and include custom headers (e.g., for authentication):

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--wsEndpoint=ws://127.0.0.1:9222/devtools/browser/<id>",
        "--wsHeaders={\"Authorization\":\"Bearer YOUR_TOKEN\"}"
      ]
    }
  }
}
```

To get the WebSocket endpoint from a running Chrome instance, visit `http://127.0.0.1:9222/json/version` and look for the `webSocketDebuggerUrl` field.

You can also run `npx chrome-devtools-mcp@latest --help` to see all available configuration options.

## Concepts

### User data directory

`chrome-devtools-mcp` starts a Chrome's stable channel instance using the following user
data directory:

- Linux / macOS: `$HOME/.cache/chrome-devtools-mcp/chrome-profile-$CHANNEL`
- Windows: `%HOMEPATH%/.cache/chrome-devtools-mcp/chrome-profile-$CHANNEL`

The user data directory is not cleared between runs and shared across
all instances of `chrome-devtools-mcp`. Set the `isolated` option to `true`
to use a temporary user data dir instead which will be cleared automatically after
the browser is closed.

### Connecting to a running Chrome instance

By default, the Chrome DevTools MCP server will start a new Chrome instance with a dedicated profile. This might not be ideal in all situations:

- If you would like to maintain the same application state when alternating between manual site testing and agent-driven testing.
- When the MCP needs to sign into a website. Some accounts may prevent sign-in when the browser is controlled via WebDriver (the default launch mechanism for the Chrome DevTools MCP server).
- If you're running your LLM inside a sandboxed environment, but you would like to connect to a Chrome instance that runs outside the sandbox.

In these cases, start Chrome first and let the Chrome DevTools MCP server connect to it. There are two ways to do so:

- **Automatic connection (available in Chrome 144)**: best for sharing state between manual and agent-driven testing.
- **Manual connection via remote debugging port**: best when running inside a sandboxed environment.

#### Automatically connecting to a running Chrome instance

**Step 1:** Set up remote debugging in Chrome

In Chrome (\>= M144), do the following to set up remote debugging:

1.  Navigate to `chrome://inspect/#remote-debugging` to enable remote debugging.
2.  Follow the dialog UI to allow or disallow incoming debugging connections.

**Step 2:** Configure Chrome DevTools MCP server to automatically connect to a running Chrome Instance

To connect the `chrome-devtools-mcp` server to the running Chrome instance, use
`--autoConnect` command line argument for the MCP server.

The following code snippet is an example configuration for gemini-cli:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

**Step 3:** Test your setup

Make sure your browser is running. Open gemini-cli and run the following prompt:

```none
Check the performance of https://developers.chrome.com
```

> [!NOTE]
> The <code>autoConnect</code> option requires the user to start Chrome. If the user has multiple active profiles, the MCP server will connect to the default profile (as determined by Chrome). The MCP server has access to all open windows for the selected profile.

The Chrome DevTools MCP server will try to connect to your running Chrome
instance. It shows a dialog asking for user permission.

Clicking **Allow** results in the Chrome DevTools MCP server opening
[developers.chrome.com](http://developers.chrome.com) and taking a performance
trace.

#### Manual connection using port forwarding

You can connect to a running Chrome instance by using the `--browser-url` option. This is useful if you are running the MCP server in a sandboxed environment that does not allow starting a new Chrome instance.

Here is a step-by-step guide on how to connect to a running Chrome instance:

**Step 1: Configure the MCP client**

Add the `--browser-url` option to your MCP client configuration. The value of this option should be the URL of the running Chrome instance. `http://127.0.0.1:9222` is a common default.

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--browser-url=http://127.0.0.1:9222"
      ]
    }
  }
}
```

**Step 2: Start the Chrome browser**

> [!WARNING]
> Enabling the remote debugging port opens up a debugging port on the running browser instance. Any application on your machine can connect to this port and control the browser. Make sure that you are not browsing any sensitive websites while the debugging port is open.

Start the Chrome browser with the remote debugging port enabled. Make sure to close any running Chrome instances before starting a new one with the debugging port enabled. The port number you choose must be the same as the one you specified in the `--browser-url` option in your MCP client configuration.

For security reasons, [Chrome requires you to use a non-default user data directory](https://developer.chrome.com/blog/remote-debugging-port) when enabling the remote debugging port. You can specify a custom directory using the `--user-data-dir` flag. This ensures that your regular browsing profile and data are not exposed to the debugging session.

**macOS**

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable
```

**Linux**

```bash
/usr/bin/google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable
```

**Windows**

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-profile-stable"
```

**Step 3: Test your setup**

After configuring the MCP client and starting the Chrome browser, you can test your setup by running a simple prompt in your MCP client:

```
Check the performance of https://developers.chrome.com
```

Your MCP client should connect to the running Chrome instance and receive a performance report.

If you hit VM-to-host port forwarding issues, see the “Remote debugging between virtual machine (VM) and host fails” section in [`docs/troubleshooting.md`](./docs/troubleshooting.md#remote-debugging-between-virtual-machine-vm-and-host-fails).

For more details on remote debugging, see the [Chrome DevTools documentation](https://developer.chrome.com/docs/devtools/remote-debugging/).

### Debugging Chrome on Android

Please consult [these instructions](./docs/debugging-android.md).

## Known limitations

See [Troubleshooting](./docs/troubleshooting.md).

---

## Repository Overview

This repository is a monorepo that integrates standard browser automation with the **Arkhe(n)** experimental framework.

### Major Components

- **`src/`**: Core TypeScript implementation of the MCP server, featuring standard DevTools tools and Arkhe-specific extensions.
- **`arkhe-core/`**: Central networking and synchronization logic for the Arkhe PTST (Phase Topology Space-Time) nodes.
- **`src/isa/`**: Definition of the Arkhé(n) Instruction Set Architecture (ISA) in Zig, governing low-level simulation opcodes.
- **`arkhe-direnv/`**: A Go-based utility for managing coherent shell environments.
- **Mobile Integration**: Native implementations for Android and iOS nodes located in `android/` and `ios/` directories.
- **Verification Suite**: A collection of Python and TypeScript scripts in `scripts/` for validating system coherence and security.

### Ethical Mandate (EQBE)

Modules related to simulation and quantum-biological state modification are subject to the **Ethical Quantum-Biological Engineering (EQBE)** protocol defined in [`AGENTS.md`](./AGENTS.md). This includes mandatory safety audits and adherence to non-disruption "Red Lines."

For more details, consult the [Quick Start Guide](./QUICK_START_GUIDE.md) and the [Implementation Summary](./IMPLEMENTATION_SUMMARY_v3_0_OMEGA.md).
