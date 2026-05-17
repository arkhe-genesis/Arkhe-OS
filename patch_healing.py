with open("healing/expanded_healing_actions.py", "r") as f:
    content = f.read()

target_block = """    async def execute_healing(self, anomaly_alert: Dict) -> Dict:
        \"\"\"Executa ação de healing para uma anomalia.\"\"\"
        # Detect feature from alert
        target_feature = None
        for feature in self.FEATURE_HEALING_MAP.keys():
            if feature in anomaly_alert:
                target_feature = feature
                break

        if not target_feature:
            logger.warning("Nenhuma feature reconhecida para healing")
            return {"status": "failed", "reason": "no_feature_recognized"}

        # Select first action
        action = self.FEATURE_HEALING_MAP[target_feature][0]
        handler = self._action_handlers.get(action)
        if not handler:
             return {"status": "failed", "reason": "handler_not_found"}

        success = await handler(anomaly_alert)
        result = {
            "action": action.value,
            "feature": target_feature,
            "success": success,
            "timestamp": time.time()
        }
        self._healing_history.append(result)
        return result"""

new_block = """    async def execute_healing(self, anomaly_alert: Dict, action_override: Optional[ExpandedHealingAction] = None) -> Dict:
        \"\"\"Executa ação de healing para uma anomalia.\"\"\"
        # Detect feature from alert
        target_feature = None
        for feature in self.FEATURE_HEALING_MAP.keys():
            if feature in anomaly_alert:
                target_feature = feature
                break

        if not target_feature and not action_override:
            logger.warning("Nenhuma feature reconhecida para healing")
            return {"status": "failed", "reason": "no_feature_recognized"}

        # Select first action
        action = action_override if action_override else self.FEATURE_HEALING_MAP[target_feature][0]
        handler = self._action_handlers.get(action)
        if not handler:
             return {"status": "failed", "reason": "handler_not_found"}

        success = await handler(anomaly_alert)
        result = {
            "action": action.value,
            "feature": target_feature,
            "success": success,
            "timestamp": time.time()
        }
        self._healing_history.append(result)
        return result"""

if target_block in content:
    content = content.replace(target_block, new_block)
    with open("healing/expanded_healing_actions.py", "w") as f:
        f.write(content)
    print("Patched healing successfully")
else:
    print("Could not find the target block to patch healing")
