with open("substrates/t/927_permaweb_bridge/permaweb_bridge.py", "r") as f:
    content = f.read()

# Fix spawn_agent_process
old_str = """        if "id" in result or "error" in result:
            import uuid
            self._process_registry[agent_id] = {
                "process_id": result.get("id", "ao-mock-err-" + str(uuid.uuid4())[:8]),
                "created_at": datetime.now(timezone.utc).isoformat(),
            } """
new_str = """        if "id" in result or "error" in result:
            if result.get("status") == "mock_spawned" and "error" in result:
                return result
            import uuid
            self._process_registry[agent_id] = {
                "process_id": result.get("id", "ao-mock-err-" + str(uuid.uuid4())[:8]),
                "created_at": datetime.now(timezone.utc).isoformat(),
            } """
content = content.replace(old_str, new_str)

# Fix create_agent_shell
old_shell = """        if agent_id not in self._process_registry:
            spawn_result = self.aos.spawn_aos("arkhe-{0}".format(agent_id))
            if "error" in spawn_result and "id" not in spawn_result:
                return spawn_result
            self._process_registry[agent_id] = {"process_id": spawn_result.get("id")} """
new_shell = """        if agent_id not in self._process_registry:
            spawn_result = self.aos.spawn_aos("arkhe-{0}".format(agent_id))
            if "error" in spawn_result and "id" not in spawn_result:
                return spawn_result
            if spawn_result.get("status") == "mock_spawned" and "error" in spawn_result:
                return spawn_result
            self._process_registry[agent_id] = {"process_id": spawn_result.get("id")} """
content = content.replace(old_shell, new_shell)

with open("substrates/t/927_permaweb_bridge/permaweb_bridge.py", "w") as f:
    f.write(content)
