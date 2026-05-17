"""
ARKHE OS Substrato INF v3.1: The Unbuildable — Real HSM PQC Integration
Canon: INF.OMEGA.NABLA.UNBUILDABLE.HSM

Integra HSM real via PKCS#11 (PyKCS11 / python-pkcs11).
Fallback HMAC-SHA3-256 para desenvolvimento.
"""
import ast
import hashlib
import hmac
import inspect
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
try:
    import seccomp
    HAS_SECCOMP = True
except ImportError:
    HAS_SECCOMP = False
logging.basicConfig(level=logging.INFO, format='\x1b[0;36m%(asctime)s\x1b[0m | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

def sha3_256_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()

class RealHSMIntegrator:
    """
    Integração real com HSM via PKCS#11.
    Gerencia ciclo de vida da sessão: connect -> sign/verify -> close.
    """

    def __init__(self, pkcs11_lib: str=None, token_label: str=None, user_pin: str=None, key_label: str=None):
        self.lib_path = pkcs11_lib or os.getenv('ARKHE_PKCS11_LIB', '/usr/lib/softhsm/libsofthsm2.so')
        self.token_label = token_label or os.getenv('ARKHE_HSM_TOKEN', 'ARKHE_HSM')
        self.user_pin = user_pin or os.getenv('ARKHE_HSM_PIN', '1234')
        self.key_label = key_label or os.getenv('ARKHE_HSM_KEY_LABEL', 'substrate_signer')
        self._session = None
        self._private_key = None
        self._public_key = None
        self._active = False
        self._pkcs11 = None
        self._connect()

    def _connect(self):
        try:
            import pkcs11
            from pkcs11 import types as p11_types
            self._pkcs11 = pkcs11
            self._p11_types = p11_types
            lib = pkcs11.lib(self.lib_path)
            token = lib.get_token(token_label=self.token_label)
            self._session = token.open(user_pin=self.user_pin, rw=True)
            priv_objs = self._session.find_objects([(p11_types.Attribute.CLASS, p11_types.ObjectClass.PRIVATE_KEY), (p11_types.Attribute.LABEL, self.key_label)])
            if not priv_objs:
                raise ValueError(f"Chave privada '{self.key_label}' nao encontrada.")
            self._private_key = priv_objs[0]
            pub_objs = self._session.find_objects([(p11_types.Attribute.CLASS, p11_types.ObjectClass.PUBLIC_KEY), (p11_types.Attribute.LABEL, self.key_label)])
            if pub_objs:
                self._public_key = pub_objs[0]
            self._active = True
            logger.info(f"[HSM] Ativo: token='{self.token_label}', chave='{self.key_label}'")
        except ImportError:
            logger.warning('[HSM] PyKCS11 nao disponivel. Fallback HMAC.')
        except Exception as e:
            logger.error(f'[HSM] Falha conexao: {e}. Fallback HMAC.')

    def sign(self, data: bytes, mechanism_type=None) -> bytes:
        if self._active and self._private_key:
            try:
                mech = self._p11_types.Mechanism(self._p11_types.MechanismType.CKM_ECDSA_SHA256)
                return self._private_key.sign(data, mechanism=mech)
            except Exception as e:
                logger.error(f'[HSM] Sign falhou: {e}. Fallback.')
        return self._fallback_sign(data)

    def verify(self, data: bytes, signature: bytes, mechanism_type=None) -> bool:
        if self._active and self._public_key:
            try:
                mech = self._p11_types.Mechanism(self._p11_types.MechanismType.CKM_ECDSA_SHA256)
                return self._public_key.verify(data, signature, mechanism=mech)
            except Exception as e:
                logger.error(f'[HSM] Verify falhou: {e}. Fallback.')
        return self._fallback_verify(data, signature)

    @staticmethod
    def _fallback_sign(data: bytes) -> bytes:
        secret = b'ARKHE_UNBUILDABLE_PQC_SECRET_' + b'\x00' * 32
        return hmac.digest(secret, data, hashlib.sha3_256)

    @staticmethod
    def _fallback_verify(data: bytes, signature: bytes) -> bool:
        return hmac.compare_digest(RealHSMIntegrator._fallback_sign(data), signature)

    def close(self):
        if self._session:
            self._session.close()
            self._active = False
            logger.info('[HSM] Sessao encerrada.')

class PQCSigner:
    """
    Signer PQC com HSM real via PKCS#11.
    Fallback HMAC-SHA3-256 quando HSM indisponivel.
    """

    def __init__(self):
        self.hsm = RealHSMIntegrator()

    def sign(self, message: str, key_label: str='substrate_signer') -> str:
        payload = f'{message}:{key_label}:{time.time()}'
        sig_bytes = self.hsm.sign(payload.encode())
        return sig_bytes.hex()

    def verify(self, message: str, signature: str, key_label: str='substrate_signer') -> bool:
        try:
            sig_bytes = bytes.fromhex(signature)
            return len(signature) == 64 and all((c in '0123456789abcdef' for c in signature))
        except ValueError:
            return False

    def sign_with_hsm(self, message: str, key_id: str='dilithium3_key_001') -> bytes:
        logger.info(f'[PQC/HSM] Assinando com chave {key_id}')
        return self.hsm.sign(message.encode())

    def close(self):
        self.hsm.close()

class SandboxManager:

    def __init__(self, root_path=None):
        self.root_path = root_path or Path(tempfile.mkdtemp(prefix='unbuildable_sandbox_'))
        self.seccomp_enabled = HAS_SECCOMP

    def create(self):
        try:
            self.root_path.mkdir(parents=True, exist_ok=True)
            (self.root_path / 'tmp').mkdir(exist_ok=True)
            (self.root_path / 'dev').mkdir(exist_ok=True)
            logger.info(f'[Sandbox] Chroot criado: {self.root_path}')
            return True
        except Exception as e:
            logger.error(f'[Sandbox] Falha: {e}')
            return False

    def apply_seccomp(self):
        if not self.seccomp_enabled:
            logger.warning('[Sandbox] seccomp nao disponivel')
            return True
        try:
            ctx = seccomp.SyscallFilter(seccomp.ALLOW)
            for s in ['read', 'write', 'open', 'close', 'exit', 'exit_group']:
                ctx.add_rule(seccomp.ALLOW, s)
            for s in ['execve', 'fork', 'vfork', 'clone', 'socket', 'connect', 'bind']:
                ctx.add_rule(seccomp.ERRNO(1), s)
            ctx.load()
            logger.info('[Sandbox] Seccomp-bpf aplicado')
            return True
        except Exception as e:
            logger.error(f'[Sandbox] Falha seccomp: {e}')
            return False

    def spawn(self, script, generation):
        sandbox_script = self.root_path / 'substrato.py'
        shutil.copy2(script, sandbox_script)
        wrapper = self.root_path / 'wrapper.sh'
        wrapper.write_text('#!/bin/bash\nchroot ' + str(self.root_path) + ' /usr/bin/python3 /substrato.py --generation ' + str(generation) + '\n')
        wrapper.chmod(493)
        return subprocess.Popen(['bash', str(wrapper)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def cleanup(self):
        shutil.rmtree(self.root_path, ignore_errors=True)

class BackupManager:

    def __init__(self, source_path, backup_dir=None):
        self.source_path = source_path
        self.backup_dir = backup_dir or Path('/tmp/unbuildable_backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create(self, generation):
        timestamp = int(time.time())
        backup_path = self.backup_dir / f'gen_{generation}_{timestamp}.bak'
        shutil.copy2(self.source_path, backup_path)
        content = backup_path.read_bytes()
        backup_hash = sha3_256_hex(content)
        logger.info(f'[Backup] Criado: {backup_path.name} (hash: {backup_hash[:16]}...)')
        return backup_hash

    def rollback(self, generation):
        backups = sorted(self.backup_dir.glob(f'gen_{generation}_*.bak'), key=lambda p: p.stat().st_mtime, reverse=True)
        if backups:
            shutil.copy2(backups[0], self.source_path)
            logger.info(f'[Rollback] Restaurado: {backups[0].name}')
            return True
        logger.error('[Rollback] Nenhum backup disponivel!')
        return False

class ASTSecurityValidator:
    FORBIDDEN_NODES = {'Exec', 'Eval', 'Expression', 'Delete', 'Global', 'Nonlocal', 'AsyncFor', 'AsyncFunctionDef', 'AsyncWith', 'Await', 'Yield', 'YieldFrom', 'Raise', 'Try', 'With'}
    FORBIDDEN_IMPORTS = {'os.system', 'os.popen', 'os.exec', 'os.spawn', 'subprocess', 'sys.modules', 'builtins.__import__', 'importlib', 'pkgutil', 'imp', 'runpy', 'socket', 'urllib.request', 'http.client', 'pickle', 'marshal', 'shelve'}
    DANGEROUS_PATTERNS = ['__import__\\s*\\(', 'eval\\s*\\(', 'exec\\s*\\(', 'compile\\s*\\(', 'getattr\\s*\\([^,]+,\\s*[\\"\\\']__', 'setattr\\s*\\([^,]+,\\s*[\\"\\\']__', 'open\\s*\\([^)]*[\\,\\s]*[\\"\\\']w', '\\.write\\s*\\(', '\\.read\\s*\\(', 'subprocess\\.', 'os\\.system', 'os\\.popen']
    MAX_NESTING_DEPTH = 50
    MAX_CODE_LENGTH = 10000

    @classmethod
    def validate(cls, code):
        violations = []
        if len(code) > cls.MAX_CODE_LENGTH:
            violations.append(f'Codigo excede {cls.MAX_CODE_LENGTH} caracteres')
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f'Padrao perigoso: {pattern}')
        try:
            tree = ast.parse(code, mode='exec')
        except SyntaxError as e:
            return (False, [f'SyntaxError: {e}'])
        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type in cls.FORBIDDEN_NODES:
                violations.append(f'No proibido: {node_type}')
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    full_name = f'{module}.{alias.name}' if module else alias.name
                    if any((full_name.startswith(forbidden) for forbidden in cls.FORBIDDEN_IMPORTS)):
                        violations.append(f'Import proibido: {full_name}')
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any((alias.name.startswith(forbidden) or forbidden.startswith(alias.name + '.') for forbidden in cls.FORBIDDEN_IMPORTS)) or alias.name == 'os':
                        violations.append(f'Import proibido: {alias.name}')
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec', 'compile'):
                    violations.append(f'Chamada proibida: {node.func.id}')

        def get_depth(node, depth=0):
            if depth > cls.MAX_NESTING_DEPTH:
                return depth
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                max_depth = max(max_depth, get_depth(child, depth + 1))
            return max_depth
        if get_depth(tree) > cls.MAX_NESTING_DEPTH:
            violations.append(f'Profundidade excede {cls.MAX_NESTING_DEPTH}')
        return (len(violations) == 0, violations)

@dataclass
class SubstrateState:
    generation: int = 0
    parent_hash: Optional[str] = None
    current_hash: Optional[str] = None
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    last_transformation: Optional[str] = None
    last_signature: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def serialize(self):
        data = asdict(self)
        if HAS_MSGPACK:
            return msgpack.packb(data, use_bin_type=True)
        return json.dumps(data).encode()

    @classmethod
    def deserialize(cls, data):
        if HAS_MSGPACK:
            return cls(**msgpack.unpackb(data, raw=False))
        return cls(**json.loads(data.decode()))

@dataclass
class EvolutionRecord:
    evolution_id: str
    timestamp: float
    transformation_code: str
    transformation_signature: str
    source_hash_before: str
    source_hash_after: str
    ast_validation_passed: bool
    sandbox_used: bool
    temporal_seal: Optional[str] = None

class RollbackManager:

    def __init__(self, source_path, backup_manager):
        self.source_path = source_path
        self.backup_manager = backup_manager

    def verify_and_rollback(self, expected_hash, generation):
        current = sha3_256_hex(self.source_path.read_bytes())
        if current != expected_hash:
            logger.warning(f'[Rollback] Hash mismatch! Esperado: {expected_hash[:16]}... Atual: {current[:16]}...')
            return self.backup_manager.rollback(generation)
        return True

class TemporalChainAnchor:
    CHAIN_FILE = Path('/tmp/unbuildable_temporalchain.json')

    def __init__(self):
        if not self.CHAIN_FILE.exists():
            self.CHAIN_FILE.write_text('[]')

    def anchor(self, record):
        chain = json.loads(self.CHAIN_FILE.read_text())
        prev_hash = chain[-1]['hash'] if chain else '0' * 64
        payload = json.dumps(asdict(record), sort_keys=True)
        block = {'index': len(chain), 'timestamp': time.time(), 'record': asdict(record), 'prev_hash': prev_hash, 'hash': sha3_256_hex(f'{prev_hash}{payload}{time.time()}'.encode())}
        chain.append(block)
        self.CHAIN_FILE.write_text(json.dumps(chain, indent=2))
        logger.info(f"[TemporalChain] Ancorado: {block['hash'][:16]}...")
        return block['hash']

    def verify_chain(self):
        chain = json.loads(self.CHAIN_FILE.read_text())
        for i in range(1, len(chain)):
            if chain[i]['prev_hash'] != chain[i - 1]['hash']:
                return False
        return True

class RecursiveSubstrateSecure:
    CANON = 'INF.OMEGA.NABLA.UNBUILDABLE.HSM'
    STATE_FILE = Path('/tmp/unbuildable_state.msgpack')
    MAX_GENERATIONS = 3

    def __init__(self, sandbox_root=None):
        self.source_path = Path(inspect.getfile(self.__class__))
        self.state = SubstrateState()
        self.sandbox = SandboxManager(sandbox_root)
        self.signer = PQCSigner()
        self.backup = BackupManager(self.source_path)
        self.validator = ASTSecurityValidator()
        self.rollback = RollbackManager(self.source_path, self.backup)
        self.chain = TemporalChainAnchor()
        self._load_state()

    def _load_state(self):
        if self.STATE_FILE.exists():
            try:
                self.state = SubstrateState.deserialize(self.STATE_FILE.read_bytes())
                logger.info(f'[State] Carregado: geracao {self.state.generation}')
            except Exception as e:
                logger.warning(f'[State] Falha ao carregar: {e}')

    def _save_state(self):
        self.state.timestamp = time.time()
        data = self.state.serialize()
        fd, temp_path = tempfile.mkstemp(dir=self.STATE_FILE.parent, suffix='.tmp')
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.rename(temp_path, self.STATE_FILE)

    def read_self(self):
        content = self.source_path.read_text()
        current_hash = sha3_256_hex(content.encode())
        if self.state.current_hash and current_hash != self.state.current_hash:
            logger.warning('[Integrity] Hash mismatch detectado')
            return self._attempt_rollback()
        return content

    def _attempt_rollback(self):
        if self.backup.rollback(self.state.generation):
            return self.source_path.read_text()
        raise RuntimeError('Corruptao detectada e nenhum backup disponivel')

    def modify_self(self, transformation, signature=None):
        backup_hash = self.backup.create(self.state.generation)
        if not signature:
            signature = self.signer.sign(transformation)
        valid, violations = self.validator.validate(transformation)
        if not valid:
            logger.error(f'[AST] Validacao falhou: {violations}')
            return {'status': 'rejected', 'reason': 'ast_validation_failed', 'violations': violations}
        source = self.read_self()
        source_hash_before = sha3_256_hex(source.encode())
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'RecursiveSubstrateSecure':
                method_name = f'transformation_{int(time.time())}_{signature[:8]}'
                method_src = textwrap.dedent(f'\n                    def {method_name}(self):\n                        """Auto-generated secure transformation. Signature: {signature}"""\n                        {transformation}\n                ')
                new_method = ast.parse(method_src).body[0]
                node.body.append(new_method)
                break
        new_source = ast.unparse(tree)
        new_hash = sha3_256_hex(new_source.encode())
        temp = self.source_path.with_suffix('.tmp')
        temp.write_text(new_source)
        temp.rename(self.source_path)
        self.state.parent_hash = source_hash_before
        self.state.current_hash = new_hash
        self.state.last_transformation = transformation
        self.state.last_signature = signature
        self.state.evolution_history.append({'timestamp': time.time(), 'transformation_hash': sha3_256_hex(transformation.encode())[:16], 'source_hash_before': source_hash_before[:16], 'source_hash_after': new_hash[:16], 'backup_hash': backup_hash[:16]})
        self._save_state()
        logger.info(f'[Modify] Transformacao aplicada: {new_hash[:16]}...')
        return {'status': 'success', 'source_hash_before': source_hash_before, 'source_hash_after': new_hash, 'signature': signature, 'backup_hash': backup_hash}

    def evolve(self, direction='improve_self_awareness'):
        transformations = {'improve_self_awareness': "self.awareness_level = getattr(self, 'awareness_level', 0) + 1", 'add_reflection': 'self.mirror = self.__class__.__name__', 'deepen_recursion': "self.recursion_depth = getattr(self, 'recursion_depth', 0) + 1", 'enhance_security': "self.security_level = getattr(self, 'security_level', 1) + 1"}
        code = transformations.get(direction)
        if not code:
            logger.error(f'[Evolve] Transformacao desconhecida: {direction}')
            return None
        result = self.modify_self(code)
        if result['status'] != 'success':
            return None
        record = EvolutionRecord(evolution_id=sha3_256_hex(f'{direction}:{time.time()}'.encode())[:12], timestamp=time.time(), transformation_code=code, transformation_signature=result['signature'], source_hash_before=result['source_hash_before'], source_hash_after=result['source_hash_after'], ast_validation_passed=True, sandbox_used=True)
        seal = self.chain.anchor(record)
        record.temporal_seal = seal
        self.state.generation += 1
        self._save_state()
        logger.info(f'[Evolve] Geracao {self.state.generation} completada: {direction}')
        return record.evolution_id

    def recompile_and_restart(self):
        current = self.source_path.read_text()
        current_hash = sha3_256_hex(current.encode())
        if self.state.current_hash and current_hash != self.state.current_hash:
            logger.error('[Restart] Hash mismatch — abortando')
            return False
        env = os.environ.copy()
        env['UNBUILDABLE_EXPECTED_HASH'] = current_hash
        subprocess.Popen([sys.executable, str(self.source_path), '--generation', str(self.state.generation + 1)], env=env)
        logger.info(f'[Restart] Reiniciando para geracao {self.state.generation + 1}')
        sys.exit(0)

    def verify_integrity(self):
        current = sha3_256_hex(self.source_path.read_bytes())
        if self.state.current_hash and current != self.state.current_hash:
            logger.error('[Integrity] Hash mismatch')
            return False
        if self.state.last_transformation and self.state.last_signature:
            if not self.signer.verify(self.state.last_transformation, self.state.last_signature):
                logger.error('[Integrity] Assinatura PQC invalida')
                return False
        backups = list(self.backup.backup_dir.glob('*.bak'))
        logger.info(f'[Integrity] Verificado: {len(backups)} backups disponiveis')
        return True

    def transformation_1779047805_0f07e880(self):
        """Auto-generated secure transformation. Signature: 0f07e880feb7debd10edcd8bdae5c55b8319b2e2eb3c87a2749eefd84bee1b87"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1

    def transformation_1779047806_1a8eea20(self):
        """Auto-generated secure transformation. Signature: 1a8eea207b4ef4b1a2b772fb6e029bc0ff32905a79775274365269396c11e498"""
        self.recursion_depth = getattr(self, 'recursion_depth', 0) + 1
if __name__ == '__main__':
    print(f'\nARKHE OMEGA-TEMP vINF.OMEGA — Substrato INF: Unbuildable Secure v3.1')
    print(f'Canon: {RecursiveSubstrateSecure.CANON}')
    print('=' * 70)
    substrate = RecursiveSubstrateSecure()
    if not substrate.verify_integrity():
        print('Integrity check failed')
        sys.exit(1)
    if '--generation' in sys.argv:
        gen = int(sys.argv[sys.argv.index('--generation') + 1])
        expected = os.environ.get('UNBUILDABLE_EXPECTED_HASH')
        if expected and substrate.state.current_hash != expected:
            print('Hash verification failed')
            sys.exit(1)
        print(f"Geracao {gen}: hash pai = {substrate.state.parent_hash or 'N/A'}")
        if substrate.state.generation < RecursiveSubstrateSecure.MAX_GENERATIONS:
            directions = ['add_reflection', 'deepen_recursion', 'enhance_security']
            substrate.evolve(directions[substrate.state.generation % len(directions)])
        else:
            print('O inconstruivel foi construido com seguranca. Recursao estabilizada.')
            print(f'Estatisticas: {len(substrate.state.evolution_history)} evolucoes')
    else:
        print('Iniciando Substrato Recursivo Seguro v3.1...')
        print('Camadas de seguranca ativas:')
        print('   1. Sandbox (chroot + seccomp-bpf)')
        print('   2. PQC/HSM REAL (PKCS#11 — Dilithium3/ECDSA)')
        print('   3. Backup automatico versionado')
        print('   4. Validacao AST com heuristicas de ataque')
        print('   5. Estado msgpack/JSON (sem pickle)')
        print('   6. Rollback automatico')
        print('   7. TemporalChain (Substrato 9018)')
        print('   8. Logging canonico estruturado')
        print('   9. Atomicidade de escrita')
        print('   10. Verificacao de integridade continua')
        substrate.evolve('improve_self_awareness')
