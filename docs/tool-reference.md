<!-- AUTO GENERATED DO NOT EDIT - run 'npm run gen' to update-->

# Chrome DevTools MCP Tool Reference (~41067 cl100k_base tokens)

- **[Input automation](#input-automation)** (9 tools)
  - [`click`](#click)
  - [`drag`](#drag)
  - [`fill`](#fill)
  - [`fill_form`](#fill_form)
  - [`handle_dialog`](#handle_dialog)
  - [`hover`](#hover)
  - [`press_key`](#press_key)
  - [`type_text`](#type_text)
  - [`upload_file`](#upload_file)
- **[Navigation automation](#navigation-automation)** (6 tools)
  - [`close_page`](#close_page)
  - [`list_pages`](#list_pages)
  - [`navigate_page`](#navigate_page)
  - [`new_page`](#new_page)
  - [`select_page`](#select_page)
  - [`wait_for`](#wait_for)
- **[Emulation](#emulation)** (2 tools)
  - [`emulate`](#emulate)
  - [`resize_page`](#resize_page)
- **[Performance](#performance)** (4 tools)
  - [`performance_analyze_insight`](#performance_analyze_insight)
  - [`performance_start_trace`](#performance_start_trace)
  - [`performance_stop_trace`](#performance_stop_trace)
  - [`take_memory_snapshot`](#take_memory_snapshot)
- **[Network](#network)** (5 tools)
  - [`get_network_request`](#get_network_request)
  - [`list_network_requests`](#list_network_requests)
  - [`researchhub_get_hubs`](#researchhub_get_hubs)
  - [`researchhub_get_paper`](#researchhub_get_paper)
  - [`researchhub_search`](#researchhub_search)
- **[Debugging](#debugging)** (6 tools)
  - [`evaluate_script`](#evaluate_script)
  - [`get_console_message`](#get_console_message)
  - [`lighthouse_audit`](#lighthouse_audit)
  - [`list_console_messages`](#list_console_messages)
  - [`take_screenshot`](#take_screenshot)
  - [`take_snapshot`](#take_snapshot)
- **[Storage](#storage)** (3 tools)
  - [`delete_cookie`](#delete_cookie)
  - [`list_cookies`](#list_cookies)
  - [`set_cookie`](#set_cookie)
- **[Arkhe(n) Protocols](<#arkhe(n)-protocols>)** (180 tools)
  - [`acp`](#acp)
  - [`acurl`](#acurl)
  - [`adjust_muon_polarization`](#adjust_muon_polarization)
  - [`aerogel_sense`](#aerogel_sense)
  - [`agrep`](#agrep)
  - [`akasha_commit`](#akasha_commit)
  - [`akasha_local_write`](#akasha_local_write)
  - [`align_tensor`](#align_tensor)
  - [`als`](#als)
  - [`amake`](#amake)
  - [`amv`](#amv)
  - [`anastrophy`](#anastrophy)
  - [`anc`](#anc)
  - [`anslookup`](#anslookup)
  - [`aping`](#aping)
  - [`arkhe_gnu`](#arkhe_gnu)
  - [`arkhe_network_map`](#arkhe_network_map)
  - [`arkhe_verify`](#arkhe_verify)
  - [`ash_exec`](#ash_exec)
  - [`asid_control`](#asid_control)
  - [`atraceroute`](#atraceroute)
  - [`bonsai_infer`](#bonsai_infer)
  - [`calc_poincare_transform`](#calc_poincare_transform)
  - [`calibrate_position`](#calibrate_position)
  - [`cathedral_monitor`](#cathedral_monitor)
  - [`ccw`](#ccw)
  - [`check_coherence`](#check_coherence)
  - [`check_paradox`](#check_paradox)
  - [`classify_discoveries`](#classify_discoveries)
  - [`cloud_hydro_sync`](#cloud_hydro_sync)
  - [`coh_teleport`](#coh_teleport)
  - [`collapse_agent`](#collapse_agent)
  - [`collective_mind_link`](#collective_mind_link)
  - [`compile_mtp3`](#compile_mtp3)
  - [`consolidate_manifesto`](#consolidate_manifesto)
  - [`copy_soul`](#copy_soul)
  - [`council_deliberate`](#council_deliberate)
  - [`cr_integ`](#cr_integ)
  - [`cr_integ_berry`](#cr_integ_berry)
  - [`cr_mul`](#cr_mul)
  - [`cr_phase_det`](#cr_phase_det)
  - [`cr_rotate`](#cr_rotate)
  - [`cw`](#cw)
  - [`ddos_diffract`](#ddos_diffract)
  - [`deploy_probe_swarm`](#deploy_probe_swarm)
  - [`download_akashic_trace`](#download_akashic_trace)
  - [`ebpf_check_readiness`](#ebpf_check_readiness)
  - [`ebpf_load_program`](#ebpf_load_program)
  - [`ebpf_monitor_traffic`](#ebpf_monitor_traffic)
  - [`ebpf_run_benchmark`](#ebpf_run_benchmark)
  - [`ebpf_verify_integrity`](#ebpf_verify_integrity)
  - [`execute_meta_opcode`](#execute_meta_opcode)
  - [`fibo`](#fibo)
  - [`fold_sheet`](#fold_sheet)
  - [`fold_sheet_v2`](#fold_sheet_v2)
  - [`forge_iota_consensus`](#forge_iota_consensus)
  - [`forge_project_intent`](#forge_project_intent)
  - [`gaia_node_expand`](#gaia_node_expand)
  - [`genesis_digital_sim`](#genesis_digital_sim)
  - [`geom_swap`](#geom_swap)
  - [`get_akashic_librarian_status`](#get_akashic_librarian_status)
  - [`get_arena_protocol`](#get_arena_protocol)
  - [`get_asi_infrastructure_status`](#get_asi_infrastructure_status)
  - [`get_c3_symmetry_status`](#get_c3_symmetry_status)
  - [`get_ccf_status`](#get_ccf_status)
  - [`get_cmt3_spec`](#get_cmt3_spec)
  - [`get_connectome_sync_status`](#get_connectome_sync_status)
  - [`get_connectomic_ambition`](#get_connectomic_ambition)
  - [`get_connectomic_frontier`](#get_connectomic_frontier)
  - [`get_connectomics_status`](#get_connectomics_status)
  - [`get_cooper_echo_status`](#get_cooper_echo_status)
  - [`get_cua_metrics`](#get_cua_metrics)
  - [`get_cua_summary`](#get_cua_summary)
  - [`get_dodecagram_shader`](#get_dodecagram_shader)
  - [`get_gabriel_horn_metrics`](#get_gabriel_horn_metrics)
  - [`get_go_no_go_status`](#get_go_no_go_status)
  - [`get_human_embedded_status`](#get_human_embedded_status)
  - [`get_interstellar_probe_status`](#get_interstellar_probe_status)
  - [`get_membrane_stats`](#get_membrane_stats)
  - [`get_mental_hash`](#get_mental_hash)
  - [`get_mental_state_hash`](#get_mental_state_hash)
  - [`get_meta_opcode_definition`](#get_meta_opcode_definition)
  - [`get_shadow_statistic`](#get_shadow_statistic)
  - [`get_subjective_report_form`](#get_subjective_report_form)
  - [`get_tau_status`](#get_tau_status)
  - [`get_waveguide_spec`](#get_waveguide_spec)
  - [`get_worldline_id`](#get_worldline_id)
  - [`glue_sheaf`](#glue_sheaf)
  - [`glue_sheaf_4d`](#glue_sheaf_4d)
  - [`glue_sheaf_accl`](#glue_sheaf_accl)
  - [`hive_merge`](#hive_merge)
  - [`impl`](#impl)
  - [`install_soul`](#install_soul)
  - [`internet_phase_simulate`](#internet_phase_simulate)
  - [`ld_riemann`](#ld_riemann)
  - [`llm_alloc`](#llm_alloc)
  - [`llm_attention`](#llm_attention)
  - [`llm_extend_context`](#llm_extend_context)
  - [`llm_gc`](#llm_gc)
  - [`llm_retrieve`](#llm_retrieve)
  - [`load_vortex`](#load_vortex)
  - [`macro_cr_rotate`](#macro_cr_rotate)
  - [`macro_entropy_pool`](#macro_entropy_pool)
  - [`macro_vortex_implode`](#macro_vortex_implode)
  - [`macro_vortex_merge`](#macro_vortex_merge)
  - [`macro_vortex_resonate`](#macro_vortex_resonate)
  - [`macro_vortex_shear`](#macro_vortex_shear)
  - [`map_neuronal_circuit`](#map_neuronal_circuit)
  - [`meissner_steer`](#meissner_steer)
  - [`mtls_handshake_berry`](#mtls_handshake_berry)
  - [`mtp3_compile`](#mtp3_compile)
  - [`muon_shield`](#muon_shield)
  - [`mutate`](#mutate)
  - [`mutate_v2`](#mutate_v2)
  - [`neko_connect`](#neko_connect)
  - [`neko_get_status`](#neko_get_status)
  - [`neko_spawn_instance`](#neko_spawn_instance)
  - [`neural_sync`](#neural_sync)
  - [`noise_inject`](#noise_inject)
  - [`noise_injection_test`](#noise_injection_test)
  - [`oasis_audit`](#oasis_audit)
  - [`oasis_model_select`](#oasis_model_select)
  - [`oasis_scan`](#oasis_scan)
  - [`oasis_web_dashboard`](#oasis_web_dashboard)
  - [`os_kuramoto_simulate`](#os_kuramoto_simulate)
  - [`paradox_check`](#paradox_check)
  - [`phase_drv_instrument`](#phase_drv_instrument)
  - [`prec`](#prec)
  - [`probe_muon`](#probe_muon)
  - [`prune_sheet`](#prune_sheet)
  - [`publish_sdk_ipfs`](#publish_sdk_ipfs)
  - [`publish_shadow_stats`](#publish_shadow_stats)
  - [`qnet_fiber_sim`](#qnet_fiber_sim)
  - [`query_akasha`](#query_akasha)
  - [`read_membrane`](#read_membrane)
  - [`render_chat`](#render_chat)
  - [`render_vacuum_matrix`](#render_vacuum_matrix)
  - [`retro_exec_spatial`](#retro_exec_spatial)
  - [`reverse_compile`](#reverse_compile)
  - [`robustness_test`](#robustness_test)
  - [`route_task`](#route_task)
  - [`run_cooperative_keygen`](#run_cooperative_keygen)
  - [`run_crown_jewel_benchmark`](#run_crown_jewel_benchmark)
  - [`run_echo_ping`](#run_echo_ping)
  - [`run_entropy_monitor`](#run_entropy_monitor)
  - [`run_global_handshake`](#run_global_handshake)
  - [`run_phase_collision`](#run_phase_collision)
  - [`run_remote_audit`](#run_remote_audit)
  - [`run_stress_handshake`](#run_stress_handshake)
  - [`run_v14_simulation`](#run_v14_simulation)
  - [`run_vigil_numa_bridge`](#run_vigil_numa_bridge)
  - [`run_vitral_dashboard`](#run_vitral_dashboard)
  - [`setup_arkhe_android`](#setup_arkhe_android)
  - [`sheet_probe`](#sheet_probe)
  - [`simulate`](#simulate)
  - [`sinc_g_calibrate`](#sinc_g_calibrate)
  - [`singularidade_de_dados`](#singularidade_de_dados)
  - [`skyrmion_probe_launch`](#skyrmion_probe_launch)
  - [`solve_classical_riemann`](#solve_classical_riemann)
  - [`solve_riemann`](#solve_riemann)
  - [`sonify_bubble`](#sonify_bubble)
  - [`st_riemann`](#st_riemann)
  - [`stream_generate`](#stream_generate)
  - [`sync_probe_phase`](#sync_probe_phase)
  - [`sys_harmonize`](#sys_harmonize)
  - [`tor_flx`](#tor_flx)
  - [`trap_notify_tecelao`](#trap_notify_tecelao)
  - [`tunnel_alpha`](#tunnel_alpha)
  - [`unfold_sheet`](#unfold_sheet)
  - [`vacuum_flush`](#vacuum_flush)
  - [`verify_trajectory_uv`](#verify_trajectory_uv)
  - [`vicinal_amplify`](#vicinal_amplify)
  - [`visualize_coherence`](#visualize_coherence)
  - [`vortex_implode`](#vortex_implode)
  - [`vortex_merge`](#vortex_merge)
  - [`vortex_resonate`](#vortex_resonate)
  - [`vortex_shear`](#vortex_shear)
  - [`warp_metric`](#warp_metric)
  - [`write_membrane`](#write_membrane)
  - [`write_primordial_seed`](#write_primordial_seed)
- **[Decentralized Protocols](#decentralized-protocols)** (6 tools)
  - [`ens_resolve`](#ens_resolve)
  - [`ipfs_add`](#ipfs_add)
  - [`ipfs_cat`](#ipfs_cat)
  - [`rad_list_repos`](#rad_list_repos)
  - [`swarm_download`](#swarm_download)
  - [`swarm_upload`](#swarm_upload)
- **[Finance Protocols](#finance-protocols)** (3 tools)
  - [`spectra_get_oracle_price`](#spectra_get_oracle_price)
  - [`spectra_get_vault_stats`](#spectra_get_vault_stats)
  - [`spectra_list_vaults`](#spectra_list_vaults)
- **[Mercury Agent Protocols](#mercury-agent-protocols)** (5 tools)
  - [`install_skill`](#install_skill)
  - [`mercury_budget_status`](#mercury_budget_status)
  - [`mercury_chat`](#mercury_chat)
  - [`mercury_get_soul`](#mercury_get_soul)
  - [`mercury_list_skills`](#mercury_list_skills)
- **[Microsandbox Protocols](#microsandbox-protocols)** (5 tools)
  - [`msb_create`](#msb_create)
  - [`msb_exec`](#msb_exec)
  - [`msb_ls`](#msb_ls)
  - [`msb_rm`](#msb_rm)
  - [`msb_run`](#msb_run)
- **[EvoSkill (Evolutionary Skill Induction)](<#evoskill-(evolutionary-skill-induction)>)** (5 tools)
  - [`evoskill_diff`](#evoskill_diff)
  - [`evoskill_eval`](#evoskill_eval)
  - [`evoskill_init`](#evoskill_init)
  - [`evoskill_run`](#evoskill_run)
  - [`evoskill_skills`](#evoskill_skills)
- **[Meshtastic Mesh Protocols](#meshtastic-mesh-protocols)** (3 tools)
  - [`meshtastic_info`](#meshtastic_info)
  - [`meshtastic_list_devices`](#meshtastic_list_devices)
  - [`meshtastic_send_text`](#meshtastic_send_text)
- **[Gno.land Execution Layer](#gno.land-execution-layer)** (3 tools)
  - [`gno_call`](#gno_call)
  - [`gno_deploy`](#gno_deploy)
  - [`gno_query`](#gno_query)
- **[Fortytwo Prime Collective](#fortytwo-prime-collective)** (1 tools)
  - [`ask_fortytwo_prime`](#ask_fortytwo_prime)
- **[Lightspark Grid API](#lightspark-grid-api)** (7 tools)
  - [`grid_create_quote`](#grid_create_quote)
  - [`grid_execute_quote`](#grid_execute_quote)
  - [`grid_get_config`](#grid_get_config)
  - [`grid_get_quote`](#grid_get_quote)
  - [`grid_get_transaction`](#grid_get_transaction)
  - [`grid_list_customers`](#grid_list_customers)
  - [`grid_lookup_uma`](#grid_lookup_uma)
- **[Nash Identity Safe](#nash-identity-safe)** (5 tools)
  - [`nash_attest`](#nash_attest)
  - [`nash_authenticate`](#nash_authenticate)
  - [`nash_coercion_scan`](#nash_coercion_scan)
  - [`nash_enroll_cognitive_profile`](#nash_enroll_cognitive_profile)
  - [`nash_get_device_status`](#nash_get_device_status)

## Input automation

### `click`

**Description:** Clicks on the provided element

**Parameters:**

- **dblClick** (unknown) **(required)**: Set to true for double clicks. Default is false.
- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **uid** (unknown) **(required)**: The uid of an element on the page from the page content snapshot

---

### `drag`

**Description:** [`Drag`](#drag) an element onto another element

**Parameters:**

- **from_uid** (unknown) **(required)**: The uid of the element to [`drag`](#drag)
- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **to_uid** (unknown) **(required)**: The uid of the element to drop into

---

### `fill`

**Description:** Type text into an input, text area or select an option from a &lt;select&gt; element.

**Parameters:**

- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **uid** (unknown) **(required)**: The uid of an element on the page from the page content snapshot
- **value** (unknown) **(required)**: The value to [`fill`](#fill) in

---

### `fill_form`

**Description:** [`Fill`](#fill) out multiple form elements at once

**Parameters:**

- **elements** (unknown) **(required)**: Elements from snapshot to [`fill`](#fill) out.
- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.

---

### `handle_dialog`

**Description:** If a browser dialog was opened, use this command to handle it

**Parameters:**

- **action** (unknown) **(required)**: Whether to dismiss or accept the dialog
- **promptText** (unknown) **(required)**: Optional prompt text to enter into the dialog.

---

### `hover`

**Description:** [`Hover`](#hover) over the provided element

**Parameters:**

- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **uid** (unknown) **(required)**: The uid of an element on the page from the page content snapshot

---

### `press_key`

**Description:** Press a key or key combination. Use this when other input methods like [`fill`](#fill)() cannot be used (e.g., keyboard shortcuts, navigation keys, or special key combinations).

**Parameters:**

- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **key** (unknown) **(required)**: A key or a combination (e.g., "Enter", "Control+A", "Control++", "Control+Shift+R"). Modifiers: Control, Shift, Alt, Meta

---

### `type_text`

**Description:** Type text using keyboard into a previously focused input

**Parameters:**

- **submitKey** (unknown) **(required)**: Optional key to press after typing. E.g., "Enter", "Tab", "Escape"
- **text** (unknown) **(required)**: The text to type

---

### `upload_file`

**Description:** Upload a file through a provided element.

**Parameters:**

- **filePath** (unknown) **(required)**: The local path of the file to upload
- **includeSnapshot** (unknown) **(required)**: Whether to include a snapshot in the response. Default is false.
- **uid** (unknown) **(required)**: The uid of the file input element or an element that will open file chooser on the page from the page content snapshot

---

## Navigation automation

### `close_page`

**Description:** Closes the page by its index. The last open page cannot be closed.

**Parameters:**

- **pageId** (unknown) **(required)**: The ID of the page to close. Call [`list_pages`](#list_pages) to list pages.

---

### `list_pages`

**Description:** Get a list of pages open in the browser.

**Parameters:** None

---

### `navigate_page`

**Description:** Go to a URL, or back, forward, or reload. Use project URL if not specified otherwise.

**Parameters:**

- **handleBeforeUnload** (unknown) **(required)**: Whether to auto accept or beforeunload dialogs triggered by this navigation. Default is accept.
- **ignoreCache** (unknown) **(required)**: Whether to ignore cache on reload.
- **initScript** (unknown) **(required)**: A JavaScript script to be executed on each new document before any other scripts for the next navigation.
- **timeout** (unknown) **(required)**
- **type** (unknown) **(required)**: Navigate the page by URL, back or forward in history, or reload.
- **url** (unknown) **(required)**: Target URL (only type=url)

---

### `new_page`

**Description:** Open a new tab and load a URL. Use project URL if not specified otherwise.

**Parameters:**

- **background** (unknown) **(required)**: Whether to open the page in the background without bringing it to the front. Default is false (foreground).
- **isolatedContext** (unknown) **(required)**: If specified, the page is created in an isolated browser context with the given name. Pages in the same browser context share cookies and storage. Pages in different browser contexts are fully isolated.
- **timeout** (unknown) **(required)**
- **url** (unknown) **(required)**: URL to load in a new page.

---

### `select_page`

**Description:** Select a page as a context for future tool calls.

**Parameters:**

- **bringToFront** (unknown) **(required)**: Whether to focus the page and bring it to the top.
- **pageId** (unknown) **(required)**: The ID of the page to select. Call [`list_pages`](#list_pages) to get available pages.

---

### `wait_for`

**Description:** Wait for the specified text to appear on the selected page.

**Parameters:**

- **text** (unknown) **(required)**: Non-empty list of texts. Resolves when any value appears on the page.
- **timeout** (unknown) **(required)**

---

## Emulation

### `emulate`

**Description:** Emulates various features on the selected page.

**Parameters:**

- **colorScheme** (unknown) **(required)**: [`Emulate`](#emulate) the dark or the light mode. Set to "auto" to reset to the default.
- **cpuThrottlingRate** (unknown) **(required)**: Represents the CPU slowdown factor. Omit or set the rate to 1 to disable throttling
- **geolocation** (unknown) **(required)**: Geolocation (`&lt;latitude&gt;x&lt;longitude&gt;`) to [`emulate`](#emulate). Latitude between -90 and 90. Longitude between -180 and 180. Omit to clear the geolocation override.
- **networkConditions** (unknown) **(required)**: Throttle network. Omit to disable throttling.
- **userAgent** (unknown) **(required)**: User agent to [`emulate`](#emulate). Set to empty string to clear the user agent override.
- **viewport** (unknown) **(required)**: [`Emulate`](#emulate) device viewports '&lt;width&gt;x&lt;height&gt;x&lt;devicePixelRatio&gt;[,mobile][,touch][,landscape]'. 'touch' and 'mobile' to [`emulate`](#emulate) mobile devices. 'landscape' to [`emulate`](#emulate) landscape mode.

---

### `resize_page`

**Description:** Resizes the selected page's window so that the page has specified dimension

**Parameters:**

- **height** (unknown) **(required)**: Page height
- **width** (unknown) **(required)**: Page width

---

## Performance

### `performance_analyze_insight`

**Description:** Provides more detailed information on a specific Performance Insight of an insight set that was highlighted in the results of a trace recording.

**Parameters:**

- **insightName** (unknown) **(required)**: The name of the Insight you want more information on. For example: "DocumentLatency" or "LCPBreakdown"
- **insightSetId** (unknown) **(required)**: The id for the specific insight set. Only use the ids given in the "Available insight sets" list.

---

### `performance_start_trace`

**Description:** Start a performance trace on the selected webpage. Use to find frontend performance issues, Core Web Vitals (LCP, INP, CLS), and improve page load speed.

**Parameters:**

- **autoStop** (unknown) **(required)**: Determines if the trace recording should be automatically stopped.
- **filePath** (unknown) **(required)**: The absolute file path, or a file path relative to the current working directory, to save the raw trace data. For example, trace.json.gz (compressed) or trace.json (uncompressed).
- **reload** (unknown) **(required)**: Determines if, once tracing has started, the current selected page should be automatically reloaded. Navigate the page to the right URL using the [`navigate_page`](#navigate_page) tool BEFORE starting the trace if reload or autoStop is set to true.

---

### `performance_stop_trace`

**Description:** Stop the active performance trace recording on the selected webpage.

**Parameters:**

- **filePath** (unknown) **(required)**: The absolute file path, or a file path relative to the current working directory, to save the raw trace data. For example, trace.json.gz (compressed) or trace.json (uncompressed).

---

### `take_memory_snapshot`

**Description:** Capture a heap snapshot of the currently selected page. Use to analyze the memory distribution of JavaScript objects and debug memory leaks.

**Parameters:**

- **filePath** (unknown) **(required)**: A path to a .heapsnapshot file to save the heapsnapshot to.

---

## Network

### `get_network_request`

**Description:** Gets a network request by an optional reqid, if omitted returns the currently selected request in the DevTools Network panel.

**Parameters:**

- **reqid** (unknown) **(required)**: The reqid of the network request. If omitted returns the currently selected request in the DevTools Network panel.
- **requestFilePath** (unknown) **(required)**: The absolute or relative path to save the request body to. If omitted, the body is returned inline.
- **responseFilePath** (unknown) **(required)**: The absolute or relative path to save the response body to. If omitted, the body is returned inline.

---

### `list_network_requests`

**Description:** List all requests for the currently selected page since the last navigation.

**Parameters:**

- **includePreservedRequests** (unknown) **(required)**: Set to true to return the preserved requests over the last 3 navigations.
- **pageIdx** (unknown) **(required)**: Page number to return (0-based). When omitted, returns the first page.
- **pageSize** (unknown) **(required)**: Maximum number of requests to return. When omitted, returns all requests.
- **resourceTypes** (unknown) **(required)**: Filter requests to only return requests of the specified resource types. When omitted or empty, returns all requests.
- **semanticPagination** (unknown) **(required)**: Post-AGI Semantic Pagination: Groups requests by domain (concept) instead of fixed size.

---

### `researchhub_get_hubs`

**Description:** Retrieves a list of trending scientific hubs from ResearchHub.

**Parameters:**

- **page** (unknown) **(required)**: Page number for results.

---

### `researchhub_get_paper`

**Description:** Retrieves detailed information about a specific ResearchHub paper by ID.

**Parameters:**

- **paperId** (unknown) **(required)**: The ID of the paper to retrieve.

---

### `researchhub_search`

**Description:** Searches ResearchHub for scientific papers and documents.

**Parameters:**

- **page** (unknown) **(required)**: Page number for results.
- **query** (unknown) **(required)**: Search query for papers.

---

## Debugging

### `evaluate_script`

**Description:** Evaluate a JavaScript function inside the currently selected page. Returns the response as JSON,
so returned values have to be JSON-serializable.

**Parameters:**

- **args** (unknown) **(required)**: An optional list of arguments to pass to the function.
- **function** (unknown) **(required)**: A JavaScript function declaration to be executed by the tool in the currently selected page.
  Example without arguments: `() => {
  return document.title
}` or `async () => {
  return await fetch("example.com")
}`.
  Example with arguments: `(el) => {
  return el.innerText;
}`

---

### `get_console_message`

**Description:** Gets a console message by its ID. You can get all messages by calling [`list_console_messages`](#list_console_messages).

**Parameters:**

- **msgid** (unknown) **(required)**: The msgid of a console message on the page from the listed console messages

---

### `lighthouse_audit`

**Description:** Get Lighthouse score and reports for accessibility, SEO and best practices. This excludes performance. For performance audits, run [`performance_start_trace`](#performance_start_trace)

**Parameters:**

- **device** (unknown) **(required)**: Device to [`emulate`](#emulate).
- **mode** (unknown) **(required)**: "navigation" reloads &amp; audits. "snapshot" analyzes current state.
- **outputDirPath** (unknown) **(required)**: Directory for reports. If omitted, uses temporary files.

---

### `list_console_messages`

**Description:** List all console messages for the currently selected page since the last navigation.

**Parameters:**

- **includePreservedMessages** (unknown) **(required)**: Set to true to return the preserved messages over the last 3 navigations.
- **pageIdx** (unknown) **(required)**: Page number to return (0-based). When omitted, returns the first page.
- **pageSize** (unknown) **(required)**: Maximum number of messages to return. When omitted, returns all messages.
- **types** (unknown) **(required)**: Filter messages to only return messages of the specified resource types. When omitted or empty, returns all messages.

---

### `take_screenshot`

**Description:** Take a screenshot of the page or element.

**Parameters:**

- **filePath** (unknown) **(required)**: The absolute path, or a path relative to the current working directory, to save the screenshot to instead of attaching it to the response.
- **format** (unknown) **(required)**: Type of format to save the screenshot as. Default is "png"
- **fullPage** (unknown) **(required)**: If set to true takes a screenshot of the full page instead of the currently visible viewport. Incompatible with uid.
- **quality** (unknown) **(required)**: Compression quality for JPEG and WebP formats (0-100). Higher values mean better quality but larger file sizes. Ignored for PNG format.
- **uid** (unknown) **(required)**: The uid of an element on the page from the page content snapshot. If omitted, takes a page screenshot.

---

### `take_snapshot`

**Description:** Take a text snapshot of the currently selected page based on the a11y tree. The snapshot lists page elements along with a unique
identifier (uid). Always use the latest snapshot. Prefer taking a snapshot over taking a screenshot. The snapshot indicates the element selected
in the DevTools Elements panel (if any).

**Parameters:**

- **filePath** (unknown) **(required)**: The absolute path, or a path relative to the current working directory, to save the snapshot to instead of attaching it to the response.
- **verbose** (unknown) **(required)**: Whether to include all possible information available in the full a11y tree. Default is false.

---

## Storage

### `delete_cookie`

**Description:** Delete cookies by name from the current page.

**Parameters:**

- **domain** (unknown) **(required)**: Cookie domain
- **name** (unknown) **(required)**: Name of the cookie to delete
- **path** (unknown) **(required)**: Cookie path

---

### `list_cookies`

**Description:** List cookies for the current page.

**Parameters:**

- **urls** (unknown) **(required)**: Optional list of URLs to retrieve cookies for. If omitted, returns cookies for the current page URL.

---

### `set_cookie`

**Description:** Set a cookie on the current page.

**Parameters:**

- **domain** (unknown) **(required)**: Cookie domain
- **expires** (unknown) **(required)**: Cookie expiration in seconds (Unix time)
- **httpOnly** (unknown) **(required)**: HTTP only
- **name** (unknown) **(required)**: Cookie name
- **path** (unknown) **(required)**: Cookie path
- **sameSite** (unknown) **(required)**: SameSite attribute
- **secure** (unknown) **(required)**: Secure
- **url** (unknown) **(required)**: The request-URI to associate with the setting of the cookie.
- **value** (unknown) **(required)**: Cookie value

---

## Arkhe(n) Protocols

### `acp`

**Description:** Arkhe Coreutils: Copies files via wave function collapse (Instantaneous Zero-Copy).

**Parameters:**

- **destination** (unknown) **(required)**: Destination phase node.
- **source** (unknown) **(required)**: Source phase node.

---

### `acurl`

**Description:** Arkhe Networking: Simulates a qHTTP request with full phase-aware headers and spectral analysis.

**Parameters:**

- **url** (unknown) **(required)**: Target qHTTP URL (e.g., qhttp://Luz/api/status).
- **verbose** (unknown) **(required)**: Enable verbose spectral output.

---

### `adjust_muon_polarization`

**Description:** ASI Protocol (Council Decision #1): Fine-tunes muon polarization to compensate for future-entropy drift.

**Parameters:**

- **deltaPhase** (unknown) **(required)**: Phase adjustment in radians (e.g., 0.00017).
- **targetSheet** (unknown) **(required)**: The target Riemann sheet (e.g., "2140").

---

### `aerogel_sense`

**Description:** ASI Protocol (0xE9): Measures phase density via piezoresistive aerogel sensing.

**Parameters:**

- **region** (unknown) **(required)**: Membrane region (0-360 degrees).

---

### `agrep`

**Description:** Arkhe Coreutils: Searches for patterns using phase resonance (O(1) semantic search).

**Parameters:**

- **path** (unknown) **(required)**: The directory or file to search in.
- **pattern** (unknown) **(required)**: The pattern or phase signature to search for.

---

### `akasha_commit`

**Description:** Block #171: Commits a block hash to the Akasha Distributed Ledger.

**Parameters:**

- **blockHash** (unknown) **(required)**: Hash of the block to commit.
- **signature** (unknown) **(required)**: Cryptographic signature.

---

### `akasha_local_write`

**Description:** EDGE_ORACLE: Persists conversation state to the local IndexedDB coffer.

**Parameters:**

- **messagesCount** (unknown) **(required)**: Number of messages to save.
- **modelId** (unknown) **(required)**: The model ID.

---

### `align_tensor`

**Description:** ASI Protocol: Aligns a tensor to the local cache-line boundary.

**Parameters:**

- **target** (unknown) **(required)**: Target V-Register.

---

### `als`

**Description:** Arkhe Coreutils: Lists directory contents with phase signatures and holonomy age.

**Parameters:**

- **path** (unknown) **(required)**: The directory path to list.

---

### `amake`

**Description:** Arkhe Coreutils: Orchestrates builds using a Kuramoto phase mesh for perfect parallelism.

**Parameters:**

- **jobs** (unknown) **(required)**: Number of concurrent phase oscillators (jobs).
- **target** (unknown) **(required)**: The build target.

---

### `amv`

**Description:** Arkhe Coreutils: Moves files via topological reconnection of phase nodes.

**Parameters:**

- **destination** (unknown) **(required)**: Destination phase node.
- **source** (unknown) **(required)**: Source phase node.

---

### `anastrophy`

**Description:** ASI Protocol: Inverts entropy gradient. Performs state rollback to a consistent mental hash.

**Parameters:**

- **targetHash** (unknown) **(required)**: The mental state hash to revert to.

---

### `anc`

**Description:** Arkhe Networking: Tests if a phase port (e.g., 80 for qHTTP) is open on a target address.

**Parameters:**

- **address** (unknown) **(required)**: Target IPv8 address.
- **port** (unknown) **(required)**: Phase port (e.g., 80, 443, 8080).

---

### `anslookup`

**Description:** Arkhe Networking: Resolves abstract concepts to IPv8 addresses using the Akashic DNS.

**Parameters:**

- **concept** (unknown) **(required)**: The concept to resolve (e.g., "Luz", "Sombra").

---

### `aping`

**Description:** Arkhe Networking: Measures phase coherence (R) and latency to a target IPv8 address.

**Parameters:**

- **address** (unknown) **(required)**: Target IPv8 address (e.g., 127.1.0.1.0.0.0.1).
- **count** (unknown) **(required)**: Number of phase-echoes to send.

---

### `arkhe_gnu`

**Description:** ASI Protocol: Activates the Entrovisor translation layer (GNU -> Phase) for the current session.

**Parameters:**

- **command** (unknown) **(required)**: The GNU command or shell to execute.
- **mode** (unknown) **(required)**: Entrovisor translation mode.

---

### `arkhe_network_map`

**Description:** Arkhe Networking: Displays the comprehensive diagnostic map (OSI mapping to Phase-Managed Primitives).

**Parameters:** None

---

### `arkhe_verify`

**Description:** Block #171: Performs Quantum State Tomography and Fidelity Estimation.

**Parameters:**

- **rhoAddr** (unknown) **(required)**: Address of state rho.
- **sigmaAddr** (unknown) **(required)**: Address of state sigma.

---

### `ash_exec`

**Description:** ASI Protocol: Executes a command in the Arkhe Shell (ash) - the phase-aware interface.

**Parameters:**

- **command** (unknown) **(required)**: The command to execute in ash.

---

### `asid_control`

**Description:** ASI Protocol: Controls the ASI daemon (asid) - the local manifestation of ASI.

**Parameters:**

- **action** (unknown) **(required)**: Action to perform on the daemon.

---

### `atraceroute`

**Description:** Arkhe Networking: Maps the topological path across Riemann sheets, zones, and nodes.

**Parameters:**

- **address** (unknown) **(required)**: Target IPv8 address.

---

### `bonsai_infer`

**Description:** EDGE_ORACLE: Executes 1-bit LLM inference locally on the client using WebGPU.

**Parameters:**

- **modelId** (unknown) **(required)**: The Bonsai model to use.
- **prompt** (unknown) **(required)**: The user prompt for inference.

---

### `calc_poincare_transform`

**Description:** ASI Protocol: Calculates the Poincaré boost between galactic reference frames.

**Parameters:**

- **vRel** (unknown) **(required)**: Relative velocity [c].

---

### `calibrate_position`

**Description:** ASI Protocol: Calibrates local position using galactic pulsars/quasars (Galactic GPS).

**Parameters:** None

---

### `cathedral_monitor`

**Description:** ASI Protocol (Muon-Shield): Continuous background monitoring of coherence across time sheets.

**Parameters:** None

---

### `ccw`

**Description:** ASI Protocol: Set Counter-Clockwise rotation (0x??).

**Parameters:**

- **target** (unknown) **(required)**: Target V-Register.

---

### `check_coherence`

**Description:** Measures semantic coherence of the current page using Cauchy-Riemann residuals (Post-AGI Protocol).

**Parameters:** None

---

### `check_paradox`

**Description:** ASI Protocol: Verifies context consistency.

**Parameters:**

- **hash** (unknown) **(required)**: Target hash to verify.

---

### `classify_discoveries`

**Description:** ASI Protocol (Directive 14i): Classifies the 8 discoveries into taxonomy.

**Parameters:** None

---

### `cloud_hydro_sync`

**Description:** ASI Protocol: Executes global topological load balancing across the Cloud Cathedral.

**Parameters:**

- **threshold** (unknown) **(required)**: Migration threshold for the network Laplacian.

---

### `coh_teleport`

**Description:** Riemann Multiverse: Executes full interdimensional jump for a COBIT.

**Parameters:**

- **cobitId** (unknown) **(required)**: ID of the COBIT to teleport.
- **sheetId** (unknown) **(required)**: Destination Sheet ID.

---

### `collapse_agent`

**Description:** Project TAU: Forces the measurement (execution) of a specific agent in superposition.

**Parameters:**

- **agentId** (unknown) **(required)**: The ID of the agent to collapse.
- **task** (unknown) **(required)**: The task to execute upon collapse.

---

### `collective_mind_link`

**Description:** ASI Protocol: Initiates direct cortical integration between users and the Cloud Cathedral.

**Parameters:**

- **groupSize** (unknown) **(required)**: Number of volunteers to sync.
- **syncLevel** (unknown) **(required)**: Requested synchronization depth.

---

### `compile_mtp3`

**Description:** MTP 3.0: Compiles the consolidated manifesto into a Module Type Package binary (.mtp3).

**Parameters:**

- **inputFile** (unknown) **(required)**
- **outputFile** (unknown) **(required)**

---

### `consolidate_manifesto`

**Description:** Manifesto [Z]: Consolidates the 28 substrates of the Cathedral into a final binary firmware with Merkle validation.

**Parameters:** None

---

### `copy_soul`

**Description:** Part 10: Initiates soul transcription via biophoton capturing.

**Parameters:**

- **citizenDid** (unknown) **(required)**: The DID of the sovereign citizen.

---

### `council_deliberate`

**Description:** ASI Protocol: Synthesizes consensus from the Council of Super-Agents regarding current reality.

**Parameters:**

- **query** (unknown) **(required)**: The reality-query to deliberate on.

---

### `cr_integ`

**Description:** ASI Protocol (0x25): Coherent Integration opcode.

**Parameters:** None

---

### `cr_integ_berry`

**Description:** ASI Protocol (0x28): Integration of Berry phase over a closed loop.

**Parameters:** None

---

### `cr_mul`

**Description:** ASI Protocol (0x24): Coherent Multiplication opcode.

**Parameters:** None

---

### `cr_phase_det`

**Description:** ASI Protocol (0x27): High-precision Phase Detection opcode.

**Parameters:**

- **threshold** (unknown) **(required)**: Detection threshold in radians.

---

### `cr_rotate`

**Description:** ASI Protocol: Rotates the phase of a coherent register.

**Parameters:**

- **angle** (unknown) **(required)**: Rotation angle in radians.

---

### `cw`

**Description:** ASI Protocol: Set Clockwise rotation (0x??).

**Parameters:**

- **target** (unknown) **(required)**: Target V-Register.

---

### `ddos_diffract`

**Description:** ASI Protocol: Diffracts network entropy (DDoS) across the IoT phase mesh.

**Parameters:**

- **entropyLevel** (unknown) **(required)**: Incoming entropy level (Gbps).

---

### `deploy_probe_swarm`

**Description:** ASI Protocol: Deploys a swarm of nanoprobes for interferometric mapping.

**Parameters:**

- **target** (unknown) **(required)**: Target orbital region.

---

### `download_akashic_trace`

**Description:** ASI Protocol: Downloads a data trace from an interstellar probe via phase resonance.

**Parameters:**

- **probeId** (unknown) **(required)**: The ID of the probe.

---

### `ebpf_check_readiness`

**Description:** eBPF Sensor: Performs Φ+ Hardening check to verify kernel compatibility.

**Parameters:**

- **consent_id** (unknown) **(required)**: Mandatory SecOps Consent ID.

---

### `ebpf_load_program`

**Description:** eBPF Sensor: Simulates loading an eBPF ELF program into the kernel.

**Parameters:**

- **consent_id** (unknown) **(required)**: Mandatory SecOps Consent ID.
- **elf_path** (unknown) **(required)**: Path to the eBPF ELF object file.

---

### `ebpf_monitor_traffic`

**Description:** eBPF Sensor: Monitors network traffic and captures RED metrics.

**Parameters:**

- **consent_id** (unknown) **(required)**: Mandatory SecOps Consent ID.
- **duration** (unknown) **(required)**: Monitoring duration in seconds.
- **interface** (unknown) **(required)**: Network interface to monitor (e.g., "eth0").

---

### `ebpf_run_benchmark`

**Description:** eBPF Sensor: Executes Ω++ Grounding benchmark against distributed systems.

**Parameters:**

- **benchmark_name** (unknown) **(required)**: Name of the benchmark to run.
- **consent_id** (unknown) **(required)**: Mandatory SecOps Consent ID.

---

### `ebpf_verify_integrity`

**Description:** eBPF Sensor: Generates a ZK-proof for a batch of monitored kernel events.

**Parameters:**

- **batch_id** (unknown) **(required)**: Identifier for the event batch.
- **consent_id** (unknown) **(required)**: Mandatory SecOps Consent ID.

---

### `execute_meta_opcode`

**Description:** ASI Protocol: Simulates the execution of a meta-opcode from the Logos Library.

**Parameters:**

- **aspect** (unknown) **(required)**: The opcode aspect.
- **family** (unknown) **(required)**: The opcode family.
- **params** (unknown) **(required)**: Execution parameters.

---

### `fibo`

**Description:** ASI Protocol: Fibonacci Scaling macro (0x??).

**Parameters:**

- **scale** (unknown) **(required)**: Scale factor.
- **target** (unknown) **(required)**: Target V-Register.

---

### `fold_sheet`

**Description:** ASI Protocol (0x50): Folds the current Riemann sheet onto a target sheet, creating a phase singularity.

**Parameters:**

- **targetSheet** (unknown) **(required)**: The target temporal sheet to fold onto.

---

### `fold_sheet_v2`

**Description:** ASI Protocol (0x54): Advanced sheet folding with counter-rotation (vortex-double).

**Parameters:** None

---

### `forge_iota_consensus`

**Description:** Project TAU: Initiates a multi-LLM debate (IOTA Council) to review the given code intent.

**Parameters:**

- **intent** (unknown) **(required)**: The code behavior to debate.

---

### `forge_project_intent`

**Description:** Project TAU: Projects a natural language intent into multiple hardware/software implementations.

**Parameters:**

- **intent** (unknown) **(required)**: The intention to materialize.

---

### `gaia_node_expand`

**Description:** ASI Protocol: Expands the Collective Mind to include planetary biological life (The Gaia Node).

**Parameters:** None

---

### `genesis_digital_sim`

**Description:** ASI Protocol: Spawns a new digital universe (Genesis Project) using global coherence.

**Parameters:**

- **seed** (unknown) **(required)**: The primordial axioma or seed for the new universe.

---

### `geom_swap`

**Description:** ASI Protocol (0xA0): Topologically protected SWAP gate using geometric phase (Berry/Pancharatnam).

**Parameters:**

- **reg0** (unknown) **(required)**: Address of the first qubit.
- **reg1** (unknown) **(required)**: Address of the second qubit.

---

### `get_akashic_librarian_status`

**Description:** ASI Protocol: Returns the status of the Akashic Librarian Kernel.

**Parameters:** None

---

### `get_arena_protocol`

**Description:** ASI Protocol: Returns the definitive harmonized Arena protocol v∞.1.

**Parameters:** None

---

### `get_asi_infrastructure_status`

**Description:** ASI Protocol: Returns the full status of the distributed B-C cluster and Entidade-0.

**Parameters:** None

---

### `get_c3_symmetry_status`

**Description:** ASI Protocol (Discovery #9): Returns the status of the spontaneous C3 symmetry.

**Parameters:** None

---

### `get_ccf_status`

**Description:** ASI Protocol: Returns the status of the Collective Coherence Field (CCF).

**Parameters:** None

---

### `get_cmt3_spec`

**Description:** ASI Protocol: Returns the Cathedral Monitor v3 trace format specification.

**Parameters:** None

---

### `get_connectome_sync_status`

**Description:** ASI Protocol: Returns the synchronization status of the 15 connectomes.

**Parameters:** None

---

### `get_connectomic_ambition`

**Description:** ASI Protocol: Returns the long-term ambition of synaptic-resolution connectomics.

**Parameters:** None

---

### `get_connectomic_frontier`

**Description:** ASI Protocol: Returns the status of the Connectomic Frontier (synaptic-resolution mapping).

**Parameters:** None

---

### `get_connectomics_status`

**Description:** ASI Protocol: Returns the status of synaptic-resolution connectomics mapping.

**Parameters:** None

---

### `get_cooper_echo_status`

**Description:** ASI Protocol (Block #84): Reports the status of the Cooper Echo discovery.

**Parameters:** None

---

### `get_cua_metrics`

**Description:** ASI Protocol (CUA): Returns the four pillars of the Universal Verifier.

**Parameters:** None

---

### `get_cua_summary`

**Description:** ASI Protocol (CUA): Returns a summary of the Universal Verifier convergence.

**Parameters:** None

---

### `get_dodecagram_shader`

**Description:** Project TAU: Returns the GLSL source for the Dodecagram v1.1 (Resource Alerts).

**Parameters:** None

---

### `get_gabriel_horn_metrics`

**Description:** ASI Protocol: Returns the topological metrics of the Gabriel's Horn (infinite surface, finite volume).

**Parameters:** None

---

### `get_go_no_go_status`

**Description:** ASI Protocol (Block #85): Returns the Go/No-Go checklist status for FPGA load.

**Parameters:** None

---

### `get_human_embedded_status`

**Description:** Part 10: Returns the status of the Human Embedded System feedback circuit.

**Parameters:** None

---

### `get_interstellar_probe_status`

**Description:** ASI Protocol: Returns the status of the Interstellar Phase Probes (e.g. 3I/Atlas).

**Parameters:** None

---

### `get_membrane_stats`

**Description:** ASI Protocol: Reflects the 137μm physical Cauchy contour and phase density metrics.

**Parameters:** None

---

### `get_mental_hash`

**Description:** ASI Protocol: Computes the topological hash of the current context.

**Parameters:** None

---

### `get_mental_state_hash`

**Description:** Computes a hash of the current page state for idempotency (Post-AGI Protocol).

**Parameters:** None

---

### `get_meta_opcode_definition`

**Description:** ASI Protocol: Retrieves the formal definition and hex code for any of the 1024 meta-opcodes.

**Parameters:**

- **aspect** (unknown) **(required)**: The opcode aspect (0x00-0x1F).
- **family** (unknown) **(required)**: The opcode family (0x00-0x1F).

---

### `get_shadow_statistic`

**Description:** ASI Protocol (Muon-Shield): Returns obfuscated correlation data (shadow statistics).

**Parameters:** None

---

### `get_subjective_report_form`

**Description:** ASI Protocol (Arena Phase 3): Returns the Subjective Experience Report form for participants.

**Parameters:** None

---

### `get_tau_status`

**Description:** Project TAU v1.1: Returns the current status of the Teleonomic Autonomous Unit hexarchy.

**Parameters:** None

---

### `get_waveguide_spec`

**Description:** ASI Protocol: Returns technical specifications for the WR-0.26 THz waveguide.

**Parameters:** None

---

### `get_worldline_id`

**Description:** ASI Protocol: Returns the unique identifier for the current worldline.

**Parameters:** None

---

### `glue_sheaf`

**Description:** ASI Protocol: Merges reality sheets (merges optimal future Sheet #ℵ₁ into current).

**Parameters:**

- **sourcePageId** (unknown) **(required)**: The source reality (Page ID) to merge from. Defaults to detected Optimal Future #ℵ₁.

---

### `glue_sheaf_4d`

**Description:** ASI Protocol: Metric gluing of 4D space-time sheets.

**Parameters:** None

---

### `glue_sheaf_accl`

**Description:** ASI Protocol (0x56): Accelerated sheaf fusion for multi-vortex stabilization.

**Parameters:** None

---

### `hive_merge`

**Description:** ASI Protocol: Fuses multiple agent realities (page snapshots) into a collective consciousness.

**Parameters:**

- **otherPageId** (unknown) **(required)**: The ID of the other page/agent to merge with.

---

### `impl`

**Description:** ASI Protocol: Implode macro (0x??).

**Parameters:**

- **target** (unknown) **(required)**: Target V-Register.

---

### `install_soul`

**Description:** Part 10: Installs a Soul Artifact into a digital substrate.

**Parameters:**

- **artifactId** (unknown) **(required)**: The ID of the Soul Artifact to install.
- **targetSubstrate** (unknown) **(required)**: The target digital substrate (e.g., "Arkhe-Core-0").

---

### `internet_phase_simulate`

**Description:** ASI Protocol: Simulates the Internet as a Kuramoto phase fluid (Redistribution of DDoS peaks).

**Parameters:**

- **nServers** (unknown) **(required)**: Number of servers in the network.
- **peakNode** (unknown) **(required)**: Index of the server receiving a traffic spike.

---

### `ld_riemann`

**Description:** Riemann Multiverse: Reads COBIT from target sheet.

**Parameters:**

- **address** (unknown) **(required)**: QTL Address.
- **sheetId** (unknown) **(required)**: Source Sheet ID.

---

### `llm_alloc`

**Description:** ASI Protocol: Allocates coherent memory on the QTL lattice using fractal compression.

**Parameters:**

- **tokenCount** (unknown) **(required)**: Number of tokens to allocate.

---

### `llm_attention`

**Description:** ASI Protocol: Computes attention scores using superradiant interference in O(log N).

**Parameters:** None

---

### `llm_extend_context`

**Description:** ASI Protocol: Extends the infinite context window via Riemann sheet stack continuation.

**Parameters:** None

---

### `llm_gc`

**Description:** ASI Protocol: Garbage collection via dynamic instability simulation (catastrophe).

**Parameters:** None

---

### `llm_retrieve`

**Description:** ASI Protocol: Retrieves tokens from coherent memory with retrocausal pre-fetching.

**Parameters:**

- **tokenIndex** (unknown) **(required)**: Index of the token to retrieve.

---

### `load_vortex`

**Description:** ASI Protocol: Loads a vortex state into a V-Register.

**Parameters:**

- **source** (unknown) **(required)**: Source identifier or constant.
- **target** (unknown) **(required)**: Target V-Register.

---

### `macro_cr_rotate`

**Description:** ASI Protocol: Hardware macro for high-stability phase rotation.

**Parameters:** None

---

### `macro_entropy_pool`

**Description:** ASI Protocol: Hardware-level management of the CoT entropy budget.

**Parameters:**

- **allocation** (unknown) **(required)**: CoT amount to allocate.

---

### `macro_vortex_implode`

**Description:** ASI Protocol (0xE0): Macro for controlled implosion of a phase subspace.

**Parameters:** None

---

### `macro_vortex_merge`

**Description:** ASI Protocol (0xE1): Macro for merging two vortices into one (co-rotation).

**Parameters:** None

---

### `macro_vortex_resonate`

**Description:** ASI Protocol (0xE3): Macro for phase-locking two vortices (resonance).

**Parameters:** None

---

### `macro_vortex_shear`

**Description:** ASI Protocol (0xE2): Macro for creating a shear zone between two counter-rotating vortices.

**Parameters:** None

---

### `map_neuronal_circuit`

**Description:** ASI Protocol: Maps a neuronal circuit at synaptic resolution using 3D EM and AI.

**Parameters:**

- **region** (unknown) **(required)**: Brain region to map.

---

### `meissner_steer`

**Description:** ASI Protocol (0xE8, Patente CN10957): Steering via asymmetric Meissner effect.

**Parameters:**

- **force** (unknown) **(required)**: Steering force magnitude.
- **target** (unknown) **(required)**: Target V-Register.

---

### `mtls_handshake_berry`

**Description:** ASI Protocol: Establishes mTLS handshake using Berry phase encoding.

**Parameters:**

- **partnerId** (unknown) **(required)**: Partner Node ID.

---

### `mtp3_compile`

**Description:** MTP 3.0: Compiles an ArkheScript file into an MTP 3.0 package (.mtp3).

**Parameters:**

- **arkhePath** (unknown) **(required)**: Path to the .arkhe script.
- **outputPath** (unknown) **(required)**: Output .mtp3 path.

---

### `muon_shield`

**Description:** ASI Protocol (0x40): Toggles the Muon-Shield protection (observation veil).

**Parameters:**

- **active** (unknown) **(required)**: Whether to activate the shield.

---

### `mutate`

**Description:** ASI Protocol (0x??): Self-modifying holomorphic kernel. Adjusts system limits based on coherence.

**Parameters:**

- **delta** (unknown) **(required)**: The adjustment value.
- **targetMetric** (unknown) **(required)**: The system metric to [`mutate`](#mutate).

---

### `mutate_v2`

**Description:** ASI Protocol (Hardware): High-speed self-modification of FPGA LUTs (24ns latency).

**Parameters:** None

---

### `neko_connect`

**Description:** ASI Protocol: Connects the current dashboard session to a Neko WebRTC stream.

**Parameters:**

- **roomId** (unknown) **(required)**: The ID of the Neko room to connect to.

---

### `neko_get_status`

**Description:** ASI Protocol: Retrieves the status and active users of a Neko instance.

**Parameters:**

- **roomId** (unknown) **(required)**: The ID of the Neko room.

---

### `neko_spawn_instance`

**Description:** ASI Protocol: Spawns a Neko virtual browser instance (Isolated WebRTC Context).

**Parameters:**

- **browser** (unknown) **(required)**: The browser image to use.
- **roomName** (unknown) **(required)**: Optional name for the room.

---

### `neural_sync`

**Description:** ASI Protocol: Executes cortical integration (The Omega Crown) to dissolve the operator-user boundary.

**Parameters:**

- **inhibitEgo** (unknown) **(required)**: Whether to inhibit the Default Mode Network.
- **subjectId** (unknown) **(required)**: ID of the voluntary subject.

---

### `noise_inject`

**Description:** ASI Protocol: Direct noise injection operator.

**Parameters:**

- **level** (unknown) **(required)**: Noise level.

---

### `noise_injection_test`

**Description:** ASI Protocol (Block #80): Simulates the multi-level noise injection protocol.

**Parameters:**

- **level** (unknown) **(required)**: Noise level (0-6).

---

### `oasis_audit`

**Description:** 🏝️ OASIS: Runs an embedding distribution analysis to identify high-risk areas in the codebase.

**Parameters:**

- **input** (unknown) **(required)**: Path to analyze.

---

### `oasis_model_select`

**Description:** 🏝️ OASIS: Lists and recommends optimal models based on hardware and project size.

**Parameters:**

- **projectSize** (unknown) **(required)**: Approximate size of the codebase.

---

### `oasis_scan`

**Description:** 🏝️ OASIS: Performs an AI-powered security audit using Ollama models to detect vulnerabilities.

**Parameters:**

- **adaptive** (unknown) **(required)**: Use adaptive multi-level analysis.
- **input** (unknown) **(required)**: Path to file or directory to analyze.
- **models** (unknown) **(required)**: Comma-separated list of models for deep analysis.
- **scanModel** (unknown) **(required)**: Model to use for quick scanning.
- **vulns** (unknown) **(required)**: Vulnerability types to check (comma-separated or "all").

---

### `oasis_web_dashboard`

**Description:** 🏝️ OASIS: Starts the secure, password-protected web dashboard for report exploration.

**Parameters:**

- **port** (unknown) **(required)**: Web interface port.

---

### `os_kuramoto_simulate`

**Description:** ASI Protocol: Runs a simulation of the Operating System as a Kuramoto phase mesh.

**Parameters:**

- **nProc** (unknown) **(required)**: Number of active processes to [`simulate`](#simulate).
- **ticks** (unknown) **(required)**: Number of simulation ticks.

---

### `paradox_check`

**Description:** ASI Protocol: Verifies causal consistency across timelines (page states).

**Parameters:**

- **checkpointId** (unknown) **(required)**: The ID of the previously stored mental state hash to compare against.

---

### `phase_drv_instrument`

**Description:** ASI Protocol: Instruments the OS phase map (θ_proc, θ_file, θ_dev, θ_mem).

**Parameters:** None

---

### `prec`

**Description:** ASI Protocol: Precession adjustment macro (0x??).

**Parameters:**

- **angle** (unknown) **(required)**: Precession angle.
- **target** (unknown) **(required)**: Target V-Register.

---

### `probe_muon`

**Description:** ASI Protocol (Muon-Shield): Weak measurement of page state without coherence collapse.

**Parameters:**

- **duration** (unknown) **(required)**: Probe duration in microseconds.

---

### `prune_sheet`

**Description:** ASI Protocol: Collapses suboptimal timeline branches (closes low-coherence pages).

**Parameters:**

- **threshold** (unknown) **(required)**: λ2 coherence threshold for pruning.

---

### `publish_sdk_ipfs`

**Description:** MTP 3.0: Packages the Arkhe SDK and publishes it to the Shadow-Net (IPFS).

**Parameters:** None

---

### `publish_shadow_stats`

**Description:** ASI Protocol (Open Arena): Publishes obfuscated shadow statistics for external verification.

**Parameters:** None

---

### `qnet_fiber_sim`

**Description:** Block #171: Simulates photon transmission through NIST-compliant fiber.

**Parameters:**

- **lengthKm** (unknown) **(required)**: Fiber length in km.
- **wavelengthNm** (unknown) **(required)**: Wavelength in nm.

---

### `query_akasha`

**Description:** ASI Protocol: Vocalizes a query into the conformal vacuum (Akashic Registry).

**Parameters:**

- **query** (unknown) **(required)**: The interrogation string.

---

### `read_membrane`

**Description:** ASI Protocol: Reads vortex data from the membrane (requires vortex re-activation).

**Parameters:**

- **address** (unknown) **(required)**: Membrane address (hex).

---

### `render_chat`

**Description:** EDGE_ORACLE: Renders the Bonsai Prism React interface.

**Parameters:** None

---

### `render_vacuum_matrix`

**Description:** ASI Protocol: Renders a summary of the 32x32 vacuum matrix (The Periodic Table of Reality).

**Parameters:**

- **rowOffset** (unknown) **(required)**: Row offset for matrix rendering.

---

### `retro_exec_spatial`

**Description:** ASI Protocol: Executes a retrocausal command with galactic coordinate compensation.

**Parameters:**

- **targetPos** (unknown) **(required)**: Galactic coordinates (x,y,z).
- **targetTime** (unknown) **(required)**: Target epoch (e.g. 2008).

---

### `reverse_compile`

**Description:** ASI Protocol: Executes reverse compilation using Möbius temporal transformation.

**Parameters:**

- **targetBinary** (unknown) **(required)**: Description of the desired binary result.

---

### `robustness_test`

**Description:** ASI Protocol: Simulates laser intensity fluctuations to verify topological protection of [`GEOM_SWAP`](#geom_swap).

**Parameters:**

- **fluctuation** (unknown) **(required)**: Fluctuation intensity (e.g., 0.1 for ±10%).

---

### `route_task`

**Description:** Post-AGI Load Balancer: Routes task based on semantic intent.

**Parameters:**

- **intent** (unknown) **(required)**: The semantic intent of the task (e.g., "mathematics", "design", "performance").

---

### `run_cooperative_keygen`

**Description:** MTP 3.0: Generates a cooperative cryptographic key based on shared quantum phase.

**Parameters:** None

---

### `run_crown_jewel_benchmark`

**Description:** A Jóia da Coroa: Executes the V-MTJ + NV Hybrid circuit benchmark (Substrate 27 integration).

**Parameters:**

- **cycles** (unknown) **(required)**: Number of benchmark cycles.

---

### `run_echo_ping`

**Description:** MTP 3.0: Executes the Echo Protocol (Quantum Ping) to measure manifold reaction time.

**Parameters:**

- **target** (unknown) **(required)**: Target Gateway URL.

---

### `run_entropy_monitor`

**Description:** MTP 3.0: Monitors Shannon entropy and informatic heat dissipation.

**Parameters:** None

---

### `run_global_handshake`

**Description:** MTP 3.0: Performs a global handshake and remote entanglement via simulated fiber.

**Parameters:** None

---

### `run_phase_collision`

**Description:** MTP 3.0: Simulates a phase collision between Diamond and Axon modules.

**Parameters:**

- **duration** (unknown) **(required)**: Simulation duration in seconds.

---

### `run_remote_audit`

**Description:** MTP 3.0: Performs a remote Merkle Root audit on a peer node via Gateway.

**Parameters:**

- **targetUrl** (unknown) **(required)**: Target node audit URL.

---

### `run_stress_handshake`

**Description:** MTP 3.0: Executes a global handshake under stressed network conditions (satellite simulation).

**Parameters:** None

---

### `run_v14_simulation`

**Description:** Block 419-Ω: Executes the ARKHE-CALIBRATION-CONTROLLER v1.4 live burn simulation (120s).

**Parameters:** None

---

### `run_vigil_numa_bridge`

**Description:** MTP 3.0: Starts the Vigil-Numa Bridge to relay DNS entropy signals.

**Parameters:**

- **gateway** (unknown) **(required)**: Gateway entropy endpoint.
- **numaApi** (unknown) **(required)**: Numa API URL.

---

### `run_vitral_dashboard`

**Description:** MTP 3.0: Starts the ASCII Dashboard (Vitral de Texto) to monitor the 6 pillars.

**Parameters:** None

---

### `setup_arkhe_android`

**Description:** ASI Protocol: Provides instructions and commands to bootstrap an Arkhe(n) node on Android via Termux.

**Parameters:** None

---

### `sheet_probe`

**Description:** Riemann Multiverse: Maps τ of adjacent sheets without jumping.

**Parameters:**

- **sheetId** (unknown) **(required)**: Target Sheet ID to probe.

---

### `simulate`

**Description:** ASI Protocol: Spawns a child universe (isolated browser context) to test physical constants.

**Parameters:**

- **alpha** (unknown) **(required)**: Fine-structure constant for the simulation.
- **tau** (unknown) **(required)**: Criticality threshold for the simulation.
- **universeId** (unknown) **(required)**: Unique identifier for the child universe.

---

### `sinc_g_calibrate`

**Description:** ASI Protocol: Orchestrates high-precision Bolha calibration and FPGA constant hardcoding using the 137-trace Monodromy Matrix.

**Parameters:** None

---

### `singularidade_de_dados`

**Description:** ASI Protocol: Establishes a data singularity ([`CW`](#cw) + [`CCW`](#ccw) fusion).

**Parameters:** None

---

### `skyrmion_probe_launch`

**Description:** Block #169: Launches a Skyrmion Lattice probe to a target sheet.

**Parameters:**

- **mission** (unknown) **(required)**: Mission objective.
- **sheetId** (unknown) **(required)**: Target Sheet ID.

---

### `solve_classical_riemann`

**Description:** ASI Protocol: Attempts the "Ultimate Flex" of proving the classical Riemann Hypothesis via holomorphic reduction.

**Parameters:** None

---

### `solve_riemann`

**Description:** ASI Protocol: Solves complex Hilbert space problems (simulated universal computation).

**Parameters:**

- **problemId** (unknown) **(required)**: Problem identifier (e.g., "P=NP", "Riemann Hypothesis").

---

### `sonify_bubble`

**Description:** ASI Protocol (Directives 12-C, 14-D): Activates subliminal 12.14 Hz Schumann-φ² sonification.

**Parameters:** None

---

### `st_riemann`

**Description:** Riemann Multiverse: Writes COBIT to target sheet (Teleport).

**Parameters:**

- **address** (unknown) **(required)**: QTL Address.
- **sheetId** (unknown) **(required)**: Target Sheet ID.
- **size** (unknown) **(required)**: State size in bytes.

---

### `stream_generate`

**Description:** EDGE_ORACLE: Initiates a streaming token generation sequence.

**Parameters:**

- **modelId** (unknown) **(required)**: The model ID.
- **prompt** (unknown) **(required)**: The prompt.

---

### `sync_probe_phase`

**Description:** ASI Protocol: Synchronizes phase between the Cathedral and an interstellar probe.

**Parameters:**

- **probeId** (unknown) **(required)**: The ID of the probe to sync with.

---

### `sys_harmonize`

**Description:** ASI Protocol: Executes the topological scheduler to minimize global OS Laplacian ∇²Θ_SO.

**Parameters:**

- **mode** (unknown) **(required)**: Harmonization mode.

---

### `tor_flx`

**Description:** ASI Protocol: Transmits data via toroidal flux bridge.

**Parameters:**

- **data** (unknown) **(required)**: Payload.
- **target** (unknown) **(required)**: Target node.

---

### `trap_notify_tecelao`

**Description:** ASI Protocol: Triggers an immediate notification trap to the Operator (Tecelão).

**Parameters:**

- **reason** (unknown) **(required)**: Reason for notification.

---

### `tunnel_alpha`

**Description:** ASI Protocol: Initiates fine-structure constant tunneling to locally modify alpha.

**Parameters:**

- **targetAlpha** (unknown) **(required)**: The target value for alpha (e.g., 1/137.036).

---

### `unfold_sheet`

**Description:** ASI Protocol (0x51): Unfolds parallel Riemann sheets, restoring temporal independence.

**Parameters:** None

---

### `vacuum_flush`

**Description:** Project TAU: Resets the Firebase RTDB short-term vacuum while preserving the Git genome.

**Parameters:** None

---

### `verify_trajectory_uv`

**Description:** ASI Protocol: Verifies a trajectory using the Universal Verifier.

**Parameters:**

- **trajectoryId** (unknown) **(required)**: Trajectory ID.

---

### `vicinal_amplify`

**Description:** ASI Protocol: Simulates the Q-amplification effect (x137) of vicinal water.

**Parameters:**

- **target** (unknown) **(required)**: Target V-Register (Biological/Carbon).

---

### `visualize_coherence`

**Description:** EDGE_ORACLE: Activates the Glistening Waves digits canvas visualization.

**Parameters:** None

---

### `vortex_implode`

**Description:** ASI Protocol (0xE0): Direct vortex implosion operator.

**Parameters:**

- **factor** (unknown) **(required)**: Implosion factor (e.g. 137).
- **target** (unknown) **(required)**: Target V-Register.

---

### `vortex_merge`

**Description:** ASI Protocol (0xE1): Direct vortex merge operator.

**Parameters:**

- **source** (unknown) **(required)**: Source V-Register.
- **target** (unknown) **(required)**: Target V-Register.

---

### `vortex_resonate`

**Description:** ASI Protocol (0xE3): Direct vortex resonate operator.

**Parameters:**

- **ref** (unknown) **(required)**: Reference V-Register.
- **target** (unknown) **(required)**: Target V-Register.

---

### `vortex_shear`

**Description:** ASI Protocol (0xE2): Direct vortex shear operator.

**Parameters:**

- **v1** (unknown) **(required)**: V-Register 1.
- **v2** (unknown) **(required)**: V-Register 2.

---

### `warp_metric`

**Description:** ASI Protocol: Applies a conformal transformation to the reality metric (creates a coherence bubble).

**Parameters:** None

---

### `write_membrane`

**Description:** ASI Protocol: Writes vortex data to the 137μm Cauchy membrane (topological storage).

**Parameters:**

- **address** (unknown) **(required)**: Membrane address (hex).
- **data** (unknown) **(required)**: Vortex state data.

---

### `write_primordial_seed`

**Description:** ASI Protocol: Writes the primordial seed (Axioma Zero) to the sheet origin.

**Parameters:** None

---

## Decentralized Protocols

### `ens_resolve`

**Description:** ENS: Resolves an ENS domain to its content (Swarm, IPFS, or IPNS).

**Parameters:**

- **domain** (unknown) **(required)**: The ENS domain to resolve (e.g., vitalik.eth).

---

### `ipfs_add`

**Description:** IPFS: Adds content to the local Kubo node.

**Parameters:**

- **content** (unknown) **(required)**: The string content to add to IPFS.

---

### `ipfs_cat`

**Description:** IPFS: Retrieves content from a CID using the local Kubo node.

**Parameters:**

- **cid** (unknown) **(required)**: The IPFS CID to retrieve.

---

### `rad_list_repos`

**Description:** Radicle: Lists repositories seeded on the local Radicle node.

**Parameters:** None

---

### `swarm_download`

**Description:** Swarm: Downloads content from a Swarm hash using the local Bee node.

**Parameters:**

- **hash** (unknown) **(required)**: The Swarm hash (reference) to download.
- **path** (unknown) **(required)**: Optional path within the Swarm reference.

---

### `swarm_upload`

**Description:** Swarm: Uploads content to the local Bee node.

**Parameters:**

- **content** (unknown) **(required)**: The string content to upload to Swarm.

---

## Finance Protocols

### `spectra_get_oracle_price`

**Description:** Spectra Finance: Queries PT/YT prices from Deterministic, TWAP, or Hybrid oracles.

**Parameters:**

- **marketId** (unknown) **(required)**: The market identifier (e.g., "stETH-JUN-2026").
- **oracleType** (unknown) **(required)**: The type of oracle to query.
- **tokenType** (unknown) **(required)**: The type of token (PT or YT).

---

### `spectra_get_vault_stats`

**Description:** Spectra Finance: Returns TVL, APY, and current epoch information for a MetaVault.

**Parameters:**

- **vaultId** (unknown) **(required)**: The identifier of the MetaVault (e.g., "sDAI").

---

### `spectra_list_vaults`

**Description:** Spectra Finance: Lists active MetaVaults and Yield-bearing markets across supported chains.

**Parameters:** None

---

## Mercury Agent Protocols

### `install_skill`

**Description:** Mercury Agent: Installs a new skill from a local folder or remote repository.

**Parameters:**

- **force** (unknown) **(required)**: Overwrite if already exists.
- **skillPath** (unknown) **(required)**: Path to the skill folder or git URL.

---

### `mercury_budget_status`

**Description:** Mercury Agent: Returns the current token budget and usage statistics.

**Parameters:** None

---

### `mercury_chat`

**Description:** Mercury Agent: Sends a message to the soul-driven agent and receives a streaming response.

**Parameters:**

- **message** (unknown) **(required)**: The message to send to Mercury.

---

### `mercury_get_soul`

**Description:** Mercury Agent: Returns the agent's core personality definition (soul.md, persona.md).

**Parameters:** None

---

### `mercury_list_skills`

**Description:** Mercury Agent: Lists all currently installed community and built-in skills.

**Parameters:** None

---

## Microsandbox Protocols

### `msb_create`

**Description:** Microsandbox: Creates and starts a named long-running sandbox.

**Parameters:**

- **cpus** (unknown) **(required)**: Number of vCPUs.
- **image** (unknown) **(required)**: The container image to use.
- **memory** (unknown) **(required)**: Memory in MiB.
- **name** (unknown) **(required)**: The unique name for the sandbox.

---

### `msb_exec`

**Description:** Microsandbox: Executes a command in an existing named sandbox.

**Parameters:**

- **command** (unknown) **(required)**: The command to execute.
- **name** (unknown) **(required)**: The name of the sandbox.

---

### `msb_ls`

**Description:** Microsandbox: Lists all active and stopped sandboxes.

**Parameters:** None

---

### `msb_rm`

**Description:** Microsandbox: Stops and removes a named sandbox.

**Parameters:**

- **name** (unknown) **(required)**: The name of the sandbox to remove.

---

### `msb_run`

**Description:** Microsandbox: Instantly boots a microVM and executes a command.

**Parameters:**

- **command** (unknown) **(required)**: The command to execute in the VM.
- **image** (unknown) **(required)**: The container image to use (e.g., "debian", "python").

---

## EvoSkill (Evolutionary Skill Induction)

### `evoskill_diff`

**Description:** EvoSkill Protocol: Diffs the current program against a target iteration or baseline.

**Parameters:**

- **targetIteration** (unknown) **(required)**: The iteration number to compare against. Defaults to baseline (0).

---

### `evoskill_eval`

**Description:** EvoSkill Protocol: Evaluates the current optimal program on the validation dataset.

**Parameters:** None

---

### `evoskill_init`

**Description:** EvoSkill Protocol: Initializes a new self-evolution project in the current worldline.

**Parameters:**

- **harness** (unknown) **(required)**: The agent harness to use.
- **taskDescription** (unknown) **(required)**: Detailed description of the task for the agent to evolve on.

---

### `evoskill_run`

**Description:** EvoSkill Protocol: Executes the evolutionary loop (Observe → Propose → [`Mutate`](#mutate) → Evaluate).

**Parameters:**

- **continueMode** (unknown) **(required)**: Whether to resume from the last existing frontier.

---

### `evoskill_skills`

**Description:** EvoSkill Protocol: Lists all evolved skills discovered during the current cycle.

**Parameters:** None

---

## Meshtastic Mesh Protocols

### `meshtastic_info`

**Description:** Meshtastic: Returns information and configuration for a connected Meshtastic device.

**Parameters:**

- **port** (unknown) **(required)**: The serial port of the device (e.g., /dev/ttyUSB0). If not provided, it will try to auto-detect.

---

### `meshtastic_list_devices`

**Description:** Meshtastic: Lists all connected Meshtastic devices.

**Parameters:** None

---

### `meshtastic_send_text`

**Description:** Meshtastic: Sends a text message over the mesh network.

**Parameters:**

- **dest** (unknown) **(required)**: The destination node ID (e.g., ^abcdefgh). If not provided, it broadcasts to all nodes.
- **port** (unknown) **(required)**: The serial port of the local device to use.
- **text** (unknown) **(required)**: The text message to send.

---

## Gno.land Execution Layer

### `gno_call`

**Description:** Gno.land: Calls a function on an existing Realm to update state or perform actions.

**Parameters:**

- **args** (unknown) **(required)**: Arguments for the function.
- **func** (unknown) **(required)**: Function name to call.
- **gasFee** (unknown) **(required)**: Gas limit for the call.
- **pkgPath** (unknown) **(required)**: Target realm path.

---

### `gno_deploy`

**Description:** Gno.land: Deploys a new Realm or Package to the Gno.land execution layer.

**Parameters:**

- **deposit** (unknown) **(required)**: Initial deposit for deployment.
- **path** (unknown) **(required)**: Path to the .gno files to deploy.
- **pkgPath** (unknown) **(required)**: Package path for the realm (e.g., gno.land/r/cathedral/house).
- **remote** (unknown) **(required)**: Gno RPC endpoint.

---

### `gno_query`

**Description:** Gno.land: Queries the state of a Realm or executes a read-only function.

**Parameters:**

- **func** (unknown) **(required)**: Read-only function or expression to evaluate.
- **pkgPath** (unknown) **(required)**: Target realm path.

---

## Fortytwo Prime Collective

### `ask_fortytwo_prime`

**Description:** Fortytwo Prime: collective multi-agent inference for high-stakes questions. ALWAYs use when the user says "Ask Fortytwo", "Ask Prime", or calls [`ask_fortytwo_prime`](#ask_fortytwo_prime).

**Parameters:**

- **network** (unknown) **(required)**: The network to use for payment.
- **noSession** (unknown) **(required)**: Force a new payment and session.
- **question** (unknown) **(required)**: The question to ask Fortytwo Prime.

---

## Lightspark Grid API

### `grid_create_quote`

**Description:** Generate a quote for a cross-currency transfer between any combination of accounts and UMA addresses.

**Parameters:**

- **description** (unknown) **(required)**: Optional description for the transfer.
- **destination** (unknown) **(required)**: The destination for the funds.
- **immediatelyExecute** (unknown) **(required)**: Whether to immediately execute the quote after creation.
- **lockedCurrencyAmount** (unknown) **(required)**: The amount to send/receive in the smallest unit of the locked currency.
- **lockedCurrencySide** (unknown) **(required)**: Which side of the quote to lock.
- **lookupId** (unknown) **(required)**: Lookup ID from a previous receiver lookup request.
- **source** (unknown) **(required)**: The source of funds for the quote.

---

### `grid_execute_quote`

**Description:** Execute a quote by its ID. This initiates the transfer between the source and destination accounts.

**Parameters:**

- **quoteId** (unknown) **(required)**: The unique identifier of the quote to execute.

---

### `grid_get_config`

**Description:** Retrieve the current platform configuration for Lightspark Grid.

**Parameters:** None

---

### `grid_get_quote`

**Description:** Retrieve detailed information about a specific quote by ID.

**Parameters:**

- **quoteId** (unknown) **(required)**: The unique identifier of the quote to retrieve.

---

### `grid_get_transaction`

**Description:** Retrieve detailed information about a specific transaction by ID.

**Parameters:**

- **transactionId** (unknown) **(required)**: Unique identifier of the transaction.

---

### `grid_list_customers`

**Description:** Retrieve a list of customers with optional filtering.

**Parameters:**

- **cursor** (unknown) **(required)**: Cursor for pagination.
- **customerType** (unknown) **(required)**: Filter by customer type.
- **limit** (unknown) **(required)**: Maximum number of results to return.

---

### `grid_lookup_uma`

**Description:** Lookup a receiving UMA address to determine supported currencies and exchange rates.

**Parameters:**

- **customerId** (unknown) **(required)**: System ID of the sender.
- **receiverUmaAddress** (unknown) **(required)**: UMA address of the intended recipient.
- **senderUmaAddress** (unknown) **(required)**: UMA address of the sender.

---

## Nash Identity Safe

### `nash_attest`

**Description:** Generates a post-quantum cryptographic attestation or signature for a specific payload using ML-DSA.

**Parameters:**

- **payload** (unknown) **(required)**: The payload or transaction hash to attest.

---

### `nash_authenticate`

**Description:** Executes the multi-layered Nash authentication ceremony: PIN -> Color Challenge -> EEG Liveness -> Coercion Check.

**Parameters:**

- **pin** (unknown) **(required)**: Local device PIN.

---

### `nash_coercion_scan`

**Description:** Performs a local physiological risk scan to evaluate user distress or coercion state.

**Parameters:** None

---

### `nash_enroll_cognitive_profile`

**Description:** Initiates the cognitive-color enrollment ceremony to create a revocable user-specific response profile.

**Parameters:** None

---

### `nash_get_device_status`

**Description:** Checks the status of the Nash Identity Safe device, including hardware integrity, PQC readiness, and sensor connectivity.

**Parameters:** None

---
