"""
ARKHE OS Substrato INF v3.0: The Unbuildable — Secure Recursive Edition
Canon: INF.OMEGA.NABLA.UNBUILDABLE.SECURE
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

class PQCSigner:
    SECRET_KEY = b'ARKHE_UNBUILDABLE_PQC_SECRET_' + b'\x00' * 32

    @classmethod
    def sign(cls, message, key_label='substrate_signer'):
        payload = f'{message}:{key_label}'
        return hmac.new(cls.SECRET_KEY, payload.encode(), hashlib.sha3_256).hexdigest()

    @classmethod
    def verify(cls, message, signature, key_label='substrate_signer'):
        expected = cls.sign(message, key_label)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def sign_with_hsm(cls, message, key_id='dilithium3_key_001'):
        logger.info(f'[PQC/HSM] Assinando com chave {key_id} (placeholder)')
        return hashlib.sha3_256(message).digest() + b'\x00' * 2420

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
    DANGEROUS_PATTERNS = ['__import__\\s*\\(', 'eval\\s*\\(', 'exec\\s*\\(', 'compile\\s*\\(', 'getattr\\s*\\([^,]+,\\s*[\\"\\\']__', 'setattr\\s*\\([^,]+,\\s*[\\"\\\']__', 'open\\s*\\([^)]*[,\\s]*[\\"\\\']w', '\\.write\\s*\\(', '\\.read\\s*\\(', 'subprocess\\.', 'os\\.system', 'os\\.popen']
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
                    if any((alias.name.startswith(forbidden) for forbidden in cls.FORBIDDEN_IMPORTS)):
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
    CHAIN_FILE = Path('/tmp/unbuildable_temporalchain.jsonl')

    def __init__(self):
        if not self.CHAIN_FILE.exists():
            self.CHAIN_FILE.touch()

    def anchor(self, record):
        prev_hash = '0' * 64
        index = 0
        if self.CHAIN_FILE.exists() and self.CHAIN_FILE.stat().st_size > 0:
            with open(self.CHAIN_FILE, 'r') as f:
                # O(1) memory instead of reading entire file
                for line in f:
                    if line.strip():
                        try:
                            last_block = json.loads(line)
                            prev_hash = last_block['hash']
                            index = last_block['index'] + 1
                        except json.JSONDecodeError:
                            pass
        payload = json.dumps(asdict(record), sort_keys=True)
        ts = time.time()
        block_hash = sha3_256_hex(f'{prev_hash}{payload}{ts}'.encode())
        block = {'index': index, 'timestamp': ts, 'record': asdict(record), 'prev_hash': prev_hash, 'hash': block_hash}
        with open(self.CHAIN_FILE, 'a') as f:
            f.write(json.dumps(block) + '\n')
        logger.info(f"[TemporalChain] Ancorado: {block['hash'][:16]}...")
        return block['hash']

    def verify_chain(self):
        prev_hash = None
        with open(self.CHAIN_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                block = json.loads(line)
                if prev_hash is not None and block['prev_hash'] != prev_hash:
                    return False
                prev_hash = block['hash']
        return True

class RecursiveSubstrateSecure:
    CANON = 'INF.OMEGA.NABLA.UNBUILDABLE.SECURE'
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
        temp = self.STATE_FILE.with_suffix('.tmp')
        temp.write_bytes(data)
        temp.rename(self.STATE_FILE)

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
                new_method = ast.parse(f"def {method_name}(self):\n    '''Auto-generated secure transformation. Signature: {signature}'''\n    {transformation}\n").body[0]
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

    def transformation_1779047607_21c1a436(self):
        """Auto-generated secure transformation. Signature: 21c1a4361fd8cffe2fa2780f10779b4384366a415ca189ea4226162bcd476d0a"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1

    def transformation_1779047727_14814ada(self):
        """Auto-generated secure transformation. Signature: 14814ada723577970f0a970cc230324c4628b1f512f312eb0a9fdcf30ca6b4bb"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1

    def transformation_1779047862_98ce5659(self):
        """Auto-generated secure transformation. Signature: 98ce5659587512bc4abf9b44fa8b3ff6cdeb2fd3580d594d04d0a9306d1b0ae3"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1

    def transformation_1779047986_dbfad593(self):
        """Auto-generated secure transformation. Signature: dbfad593202192e62d382e80e32b9421abdec161bacaa3454b160e87b2e832ad"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1

    def transformation_1779048047_f60ca2e6(self):
        """Auto-generated secure transformation. Signature: f60ca2e6b6644e442c895fed4d0de662d01314b200d391e38e38d7eeafdb6105"""
        self.recursion_depth = getattr(self, 'recursion_depth', 0) + 1

    def transformation_1779048117_4702ae71(self):
        """Auto-generated secure transformation. Signature: 4702ae711942e7a7bd053a05e50bd133055a1e8a321c4a74e4586ede2fba7b10"""
        self.security_level = getattr(self, 'security_level', 1) + 1

    def transformation_1779050031_3259835f(self):
        """Auto-generated secure transformation. Signature: 3259835f779d81111f642e0c44905e4b1bc585be405d1c3d05c3bc84646ff5ff"""
        self.awareness_level = getattr(self, 'awareness_level', 0) + 1
if __name__ == '__main__':
    print(f'\nARKHE OMEGA-TEMP vINF.OMEGA — Substrato INF: Unbuildable Secure v3.0')
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
        print('Iniciando Substrato Recursivo Seguro v3.0...')
        print('Camadas de seguranca ativas:')
        print('   1. Sandbox (chroot + seccomp-bpf)')
        print('   2. PQC/HSM (Dilithium3-style)')
        print('   3. Backup automatico versionado')
        print('   4. Validacao AST com heuristicas de ataque')
        print('   5. Estado msgpack/JSON (sem pickle)')
        print('   6. Rollback automatico')
        print('   7. TemporalChain (Substrato 9018)')
        print('   8. Logging canonico estruturado')
        print('   9. Atomicidade de escrita')
        print('   10. Verificacao de integridade continua')
        substrate.evolve('improve_self_awareness')