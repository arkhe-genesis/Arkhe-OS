import subprocess
import shutil
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum

class RuntimeType(Enum):
    PODMAN = "podman"
    DOCKER = "docker"
    CONTAINERD = "containerd"
    CRIO = "crio"
    RUNC = "runc"

@dataclass
class RuntimeInfo:
    runtime_type: RuntimeType
    version: str
    path: str
    is_rootless: bool = False
    is_daemonless: bool = False
    supports_pods: bool = False
    supports_systemd: bool = False

class RuntimeDetector:
    PREFERENCE_ORDER = [
        RuntimeType.PODMAN,
        RuntimeType.DOCKER,
        RuntimeType.CONTAINERD,
        RuntimeType.CRIO,
        RuntimeType.RUNC
    ]

    def detect_all(self) -> List[RuntimeInfo]:
        found = []
        for rt in self.PREFERENCE_ORDER:
            info = self._check_runtime(rt)
            if info:
                found.append(info)
        return found

    def get_preferred(self) -> Optional[RuntimeInfo]:
        all_runtimes = self.detect_all()
        return all_runtimes[0] if all_runtimes else None

    def _check_runtime(self, rt: RuntimeType) -> Optional[RuntimeInfo]:
        path = shutil.which(rt.value)
        if not path:
            return None

        try:
            result = subprocess.run(
                [rt.value, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip().split()[2] if result.returncode == 0 else "unknown"
        except Exception:
            version = "unknown"

        props = {
            RuntimeType.PODMAN: {
                "is_rootless": True,
                "is_daemonless": True,
                "supports_pods": True,
                "supports_systemd": True
            },
            RuntimeType.DOCKER: {
                "is_rootless": False,
                "is_daemonless": False,
                "supports_pods": False,
                "supports_systemd": False
            },
            RuntimeType.CONTAINERD: {
                "is_rootless": False,
                "is_daemonless": True,
                "supports_pods": True,
                "supports_systemd": True
            },
            RuntimeType.CRIO: {
                "is_rootless": False,
                "is_daemonless": True,
                "supports_pods": True,
                "supports_systemd": True
            },
            RuntimeType.RUNC: {
                "is_rootless": False,
                "is_daemonless": True,
                "supports_pods": False,
                "supports_systemd": False
            }
        }

        p = props.get(rt, {})
        return RuntimeInfo(
            runtime_type=rt,
            version=version,
            path=path,
            **p
        )

class UnifiedContainerCLI:
    def __init__(self, runtime: Optional[RuntimeInfo] = None):
        self.runtime = runtime or RuntimeDetector().get_preferred()
        if not self.runtime:
            raise RuntimeError("Nenhum runtime OCI encontrado no sistema")

    def build(self, image_name: str, dockerfile_path: str = ".",
              extra_args: List[str] = None) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "build", "-t", image_name]
        if extra_args:
            cmd.extend(extra_args)
        cmd.append(dockerfile_path)
        return self._run(cmd)

    def run(self, image_name: str, name: Optional[str] = None,
            ports: Dict[str, str] = None, volumes: Dict[str, str] = None,
            env: Dict[str, str] = None, detach: bool = True) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "run"]
        if detach:
            cmd.append("-d")
        if name:
            cmd.extend(["--name", name])
        if ports:
            for host, container in ports.items():
                cmd.extend(["-p", "{0}:{1}".format(host, container)])
        if volumes:
            for host, container in volumes.items():
                cmd.extend(["-v", "{0}:{1}".format(host, container)])
        if env:
            for k, v in env.items():
                cmd.extend(["-e", "{0}={1}".format(k, v)])
        cmd.append(image_name)
        return self._run(cmd)

    def exec(self, container_name: str, command: List[str]) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "exec", container_name]
        cmd.extend(command)
        return self._run(cmd)

    def stop(self, container_name: str, timeout: int = 30) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "stop", "-t", str(timeout), container_name]
        return self._run(cmd)

    def rm(self, container_name: str, force: bool = False) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_name)
        return self._run(cmd)

    def ps(self, all_containers: bool = False) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "ps"]
        if all_containers:
            cmd.append("-a")
        return self._run(cmd)

    def logs(self, container_name: str, follow: bool = False,
             tail: Optional[int] = None) -> Tuple[int, str, str]:
        cmd = [self.runtime.runtime_type.value, "logs"]
        if follow:
            cmd.append("-f")
        if tail:
            cmd.extend(["--tail", str(tail)])
        cmd.append(container_name)
        return self._run(cmd)

    def _run(self, cmd: List[str]) -> Tuple[int, str, str]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

class SecurityPolicyEnforcer:
    def __init__(self, runtime: RuntimeInfo):
        self.runtime = runtime

    def get_security_args(self) -> List[str]:
        args = []

        if self.runtime.is_rootless:
            args.append("--userns=keep-id")

        args.extend([
            "--cap-drop=ALL",
            "--cap-add=NET_BIND_SERVICE"
        ])

        args.append("--read-only")
        args.append("--security-opt=no-new-privileges:true")
        args.append("--security-opt=seccomp=/etc/arkhe/seccomp-default.json")

        return args
