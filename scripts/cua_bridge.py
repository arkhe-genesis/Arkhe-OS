#!/usr/bin/env python3
import asyncio
import json
import sys
import argparse
import base64
from typing import Any, Dict

try:
    import cua_sandbox
    from cua_sandbox import Sandbox, Image
except ImportError:
    print(json.dumps({"error": "cua-sandbox is not installed. Please run pip install cua-sandbox"}))
    sys.exit(1)

async def handle_list(args):
    try:
        sandboxes = await Sandbox.list(local=args.local)
        result = [
            {
                "name": sb.name,
                "status": sb.status,
                "os_type": sb.os_type,
                "source": sb.source,
                "created_at": sb.created_at
            }
            for sb in sandboxes
        ]
        print(json.dumps({"sandboxes": result}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

async def handle_create(args):
    try:
        if args.os == "linux":
            image = Image.linux()
        elif args.os == "macos":
            image = Image.macos()
        elif args.os == "windows":
            image = Image.windows()
        elif args.os == "android":
            image = Image.android()
        else:
            image = Image.linux()

        sb = await Sandbox.create(
            image=image,
            name=args.name,
            local=args.local,
            cpu=args.cpu,
            memory_mb=args.memory
        )
        print(json.dumps({
            "message": f"Sandbox {sb.name} created successfully.",
            "name": sb.name,
            "status": "RUNNING"
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

async def handle_run(args):
    try:
        sb = await Sandbox.connect(args.name, local=args.local)
        result = await sb.shell.run(args.command)
        print(json.dumps({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

async def handle_screenshot(args):
    try:
        sb = await Sandbox.connect(args.name, local=args.local)
        img_b64 = await sb.screenshot_base64()
        print(json.dumps({"screenshot": img_b64}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

async def handle_computer_use(args):
    try:
        sb = await Sandbox.connect(args.name, local=args.local)
        action = args.action
        params = json.loads(args.params or "{}")

        if action == "click":
            await sb.mouse.click(params.get("x"), params.get("y"), button=params.get("button", "left"))
        elif action == "type":
            await sb.keyboard.type(params.get("text", ""))
        elif action == "move":
            await sb.mouse.move(params.get("x"), params.get("y"))
        elif action == "scroll":
            await sb.mouse.scroll(params.get("x"), params.get("y"), scroll_x=params.get("scroll_x", 0), scroll_y=params.get("scroll_y", 3))
        elif action == "drag":
            await sb.mouse.drag(params.get("start_x"), params.get("start_y"), params.get("end_x"), params.get("end_y"))
        elif action == "key":
            await sb.keyboard.keypress(params.get("keys"))
        else:
            raise ValueError(f"Unknown action: {action}")

        print(json.dumps({"status": "SUCCESS", "action": action}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def main():
    parser = argparse.ArgumentParser(description="Cua Bridge CLI")
    subparsers = parser.add_subparsers(dest="command")

    # List
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--local", action="store_true")

    # Create
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--name", type=str)
    create_parser.add_argument("--os", type=str, choices=["linux", "macos", "windows", "android"], default="linux")
    create_parser.add_argument("--local", action="store_true")
    create_parser.add_argument("--cpu", type=int)
    create_parser.add_argument("--memory", type=int)

    # Run
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("name", type=str)
    run_parser.add_argument("command", type=str)
    run_parser.add_argument("--local", action="store_true")

    # Screenshot
    ss_parser = subparsers.add_parser("screenshot")
    ss_parser.add_argument("name", type=str)
    ss_parser.add_argument("--local", action="store_true")

    # Computer Use
    cu_parser = subparsers.add_parser("computer_use")
    cu_parser.add_argument("name", type=str)
    cu_parser.add_argument("action", type=str)
    cu_parser.add_argument("--params", type=str)
    cu_parser.add_argument("--local", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        asyncio.run(handle_list(args))
    elif args.command == "create":
        asyncio.run(handle_create(args))
    elif args.command == "run":
        asyncio.run(handle_run(args))
    elif args.command == "screenshot":
        asyncio.run(handle_screenshot(args))
    elif args.command == "computer_use":
        asyncio.run(handle_computer_use(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
