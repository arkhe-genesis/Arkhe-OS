import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from tools.npm_package_manager import NPMPackageManager

@pytest.fixture
def temporal_mock():
    mock = MagicMock()
    mock.anchor_event = AsyncMock()
    return mock

@pytest.fixture
def tool_system_mock():
    mock = MagicMock()
    mock.register_tool = MagicMock()
    return mock

@pytest.mark.asyncio
async def test_npm_init(temporal_mock):
    manager = NPMPackageManager(temporal=temporal_mock)

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"success stdout", b""))
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await manager.npm_init(scope="@testscope")

        mock_exec.assert_called_once_with(
            "npm", "init", "-y", "--scope=@testscope",
            cwd=str(manager.cwd),
            stdout=-1,
            stderr=-1
        )
        assert result["returncode"] == 0
        assert result["stdout"] == "success stdout"
        temporal_mock.anchor_event.assert_called_once()
        args, kwargs = temporal_mock.anchor_event.call_args
        assert args[0] == "npm_init"
        assert kwargs == {}

@pytest.mark.asyncio
async def test_npm_install(temporal_mock):
    manager = NPMPackageManager(temporal=temporal_mock)

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"install success", b""))
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await manager.npm_install(package="lodash", save_dev=True)

        mock_exec.assert_called_once_with(
            "npm", "install", "--save-dev", "lodash",
            cwd=str(manager.cwd),
            stdout=-1,
            stderr=-1
        )
        assert result["returncode"] == 0
        assert result["stdout"] == "install success"
        temporal_mock.anchor_event.assert_called_once()
        args, kwargs = temporal_mock.anchor_event.call_args
        assert args[0] == "npm_install"

@pytest.mark.asyncio
async def test_npm_run_script(temporal_mock):
    manager = NPMPackageManager(temporal=temporal_mock)

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"run start", b""))
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await manager.npm_run_script(script="start")

        mock_exec.assert_called_once_with(
            "npm", "run", "start",
            cwd=str(manager.cwd),
            stdout=-1,
            stderr=-1
        )
        assert result["returncode"] == 0
        assert result["stdout"] == "run start"
        temporal_mock.anchor_event.assert_called_once()
        args, kwargs = temporal_mock.anchor_event.call_args
        assert args[0] == "npm_run"

@pytest.mark.asyncio
async def test_npx_create_next_app(temporal_mock):
    manager = NPMPackageManager(temporal=temporal_mock)

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"next app created", b""))
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await manager.npx_create_next_app(app_name="my-app")

        mock_exec.assert_called_once_with(
            "npx", "create-next-app", "my-app", "--use-npm",
            cwd=str(manager.cwd),
            stdout=-1,
            stderr=-1
        )
        assert result["returncode"] == 0
        assert result["stdout"] == "next app created"
        temporal_mock.anchor_event.assert_called_once()
        args, kwargs = temporal_mock.anchor_event.call_args
        assert args[0] == "next_app_created"

def test_register_all_tools(tool_system_mock):
    manager = NPMPackageManager(tool_system=tool_system_mock)
    manager.register_all_tools(tool_system_mock)

    # Check that tools were registered
    assert tool_system_mock.register_tool.call_count == 10

    # Get the registered tool names to verify
    registered_tools = [
        call.args[0].tool_id for call in tool_system_mock.register_tool.call_args_list
    ]

    assert "npm_init" in registered_tools
    assert "npm_install" in registered_tools
    assert "npm_run_script" in registered_tools
    assert "npm_audit" in registered_tools
    assert "npx_create_next_app" in registered_tools
