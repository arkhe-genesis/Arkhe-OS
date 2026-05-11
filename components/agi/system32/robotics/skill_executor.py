import re

def parse_skill_contract(contract_text):
    """
    Parses a .casi skill contract to extract its properties.
    A simple parser for the lisp-like syntax provided in the prompt.

    Args:
        contract_text (str): The raw text of the .casi contract.

    Returns:
        dict: A dictionary containing extracted properties like skill_id, required_hardware.
    """
    contract_data = {}

    # Extract skill_id
    skill_id_match = re.search(r'\(skill_id:\s*string\s*=\s*"([^"]+)"\)', contract_text)
    if skill_id_match:
        contract_data['skill_id'] = skill_id_match.group(1)

    # Extract required_hardware
    hw_match = re.search(r'\(required_hardware:\s*list\s*=\s*\[(.*?)\]\)', contract_text)
    if hw_match:
        items = hw_match.group(1).split(',')
        contract_data['required_hardware'] = [item.strip().strip('"').strip("'") for item in items if item.strip()]

    # Basic structural check
    if '(contract' not in contract_text:
        raise ValueError("Invalid contract format.")

    return contract_data

def validate_agent_capability(agent_seal, required_hardware):
    """
    Validates if an agent has the required hardware.

    Args:
        agent_seal (dict): The KYM seal of the agent containing its hardware capabilities.
                           Expected format: {'capabilities': ['lidar', 'rgbd_camera', ...]}
        required_hardware (list): List of required hardware capabilities.

    Returns:
        bool: True if the agent possesses all required hardware, False otherwise.
    """
    agent_capabilities = agent_seal.get('capabilities', [])
    for hw in required_hardware:
        if hw not in agent_capabilities:
            return False
    return True
