import time
from arkhe_cobol_parse import ArkheCobolParser, ArkheCobolSecurityRules

class ArkheKernelMemoryManager:
    def __init__(self, page_size=4096, total_pages=4096):
        self.page_size = page_size
        self.total_pages = total_pages
        self.allocated_pages = 0
        self.page_faults = 0
        self.fragmentation = 0.0

    def allocate_pages(self, size_bytes):
        pages_needed = (size_bytes + self.page_size - 1) // self.page_size
        if pages_needed == 0:
            pages_needed = 1
        if self.allocated_pages + pages_needed > self.total_pages:
            self.page_faults += 1
            raise MemoryError("Out of memory")
        self.allocated_pages += pages_needed
        self.fragmentation = 0.01 * self.allocated_pages
        return pages_needed

    def map_cobol_source(self, source: str):
        size_bytes = len(source.encode('utf-8'))
        return self.allocate_pages(size_bytes)

    def free_pages(self, pages):
        self.allocated_pages = max(0, self.allocated_pages - pages)

    def get_page_fault_stats(self):
        return {"page_faults": self.page_faults, "allocated_pages": self.allocated_pages, "fragmentation": self.fragmentation}

class ArkheKernelInterruptController:
    def __init__(self):
        self.handlers = {}
        self.pending = []
        self.stats = {"raised": 0, "dispatched": 0}

    def register_handler(self, interrupt_type, handler):
        self.handlers[interrupt_type] = handler

    def raise_interrupt(self, interrupt_type, payload):
        self.stats["raised"] += 1
        self.pending.append((interrupt_type, payload))

    def dispatch_interrupts(self):
        while self.pending:
            interrupt_type, payload = self.pending.pop(0)
            self.stats["dispatched"] += 1
            if interrupt_type in self.handlers:
                self.handlers[interrupt_type](payload)

    def get_interrupt_stats(self):
        return self.stats

class ArkheKernelBusV3Interface:
    def __init__(self):
        self.channels = {}
        self.subscribers = {}
        self.stats = {"published": 0, "consumed": 0}

    def register_channel(self, name):
        self.channels[name] = []
        self.subscribers[name] = []

    def subscribe(self, channel, consumer_id):
        if channel in self.subscribers:
            self.subscribers[channel].append(consumer_id)

    def publish(self, channel, message):
        if channel in self.channels:
            self.channels[channel].append(message)
            self.stats["published"] += 1

    def consume(self, channel, consumer_id):
        if channel in self.channels and self.channels[channel]:
            self.stats["consumed"] += 1
            return self.channels[channel].pop(0)
        return None

    def get_bus_stats(self):
        return self.stats

class ArkheKernelSyscallInterface:
    def __init__(self, parser_module):
        self.parser_module = parser_module
        self.stats = {"calls": 0, "denied": 0, "types": {}}

    def execute(self, syscall_type, privilege_level, **kwargs):
        self.stats["calls"] += 1
        self.stats["types"][syscall_type] = self.stats["types"].get(syscall_type, 0) + 1

        if privilege_level == "RING3_USER" and syscall_type not in ["COBOL_PHI_C_CALC", "COBOL_AST_EXPORT"]:
            self.stats["denied"] += 1
            raise PermissionError(f"RING3 cannot invoke {syscall_type} without escalation")

        if syscall_type == "COBOL_PARSE":
            return self.parser_module.kernel_parse(kwargs["source"])
        elif syscall_type == "COBOL_EXTRACT_CICS":
            return self.parser_module._extract_cics(kwargs["source"])
        elif syscall_type == "COBOL_EXTRACT_IMS":
            return self.parser_module._extract_ims(kwargs["source"])
        elif syscall_type == "COBOL_EXTRACT_DB2":
            return self.parser_module._extract_db2(kwargs["source"])
        elif syscall_type == "COBOL_SECURITY_SCAN":
            return self.parser_module._security_scan(kwargs["source"])
        elif syscall_type == "COBOL_TOKEN_GENERATE":
            return self.parser_module._generate_tokens(kwargs["source"])
        elif syscall_type == "COBOL_PHI_C_CALC":
            return self.parser_module._calc_phi_c(kwargs["source"])
        elif syscall_type == "COBOL_AST_EXPORT":
            return self.parser_module._export_ast(kwargs["source"])
        elif syscall_type == "COBOL_VALIDATE":
            return self.parser_module._security_scan(kwargs["source"])
        elif syscall_type == "COBOL_COPYBOOK_RESOLVE":
            return []

    def get_syscall_stats(self):
        return self.stats

class ArkheKernelParserModule:
    def __init__(self):
        self.memory_manager = ArkheKernelMemoryManager()
        self.interrupt_controller = ArkheKernelInterruptController()
        self.bus = ArkheKernelBusV3Interface()
        self.syscall_interface = ArkheKernelSyscallInterface(self)
        self.parser = ArkheCobolParser()
        self.rules = ArkheCobolSecurityRules()

        self.kernel_phi_c = 1.0
        self.start_time = time.time()

        for handler in ["CICS_TXN", "IMS_CALL", "DB2_QUERY", "SECURITY_VIOLATION"]:
            self.interrupt_controller.register_handler(handler, lambda p: None)

        for channel in ["cics_transactions", "ims_calls", "db2_statements", "security_violations", "cobol_tokens", "phi_c_metrics"]:
            self.bus.register_channel(channel)

    def kernel_parse(self, source: str):
        pages = self.memory_manager.map_cobol_source(source)
        ast = self.parser.parse(source)

        cics = self._extract_cics(source)
        for c in cics:
            self.interrupt_controller.raise_interrupt("CICS_TXN", c)
            self.bus.publish("cics_transactions", c)

        ims = self._extract_ims(source)
        for i in ims:
            self.interrupt_controller.raise_interrupt("IMS_CALL", i)
            self.bus.publish("ims_calls", i)

        db2 = self._extract_db2(source)
        for d in db2:
            self.interrupt_controller.raise_interrupt("DB2_QUERY", d)
            self.bus.publish("db2_statements", d)

        violations = self._security_scan(source)
        for v in violations:
            self.interrupt_controller.raise_interrupt("SECURITY_VIOLATION", v)
            self.bus.publish("security_violations", v)
            self.kernel_phi_c -= 0.1

        tokens = self._generate_tokens(source)
        for t in tokens:
            self.bus.publish("cobol_tokens", t)

        phi_c = self._calc_phi_c(source)
        self.bus.publish("phi_c_metrics", phi_c)

        self.interrupt_controller.dispatch_interrupts()

        return {
            "ast": ast,
            "cics": cics,
            "ims": ims,
            "db2": db2,
            "violations": violations,
            "tokens": tokens,
            "phi_c": phi_c,
            "pages_allocated": pages
        }

    def _extract_cics(self, source):
        return self.parser._find_cics_transactions({}, source)

    def _extract_ims(self, source):
        return self.parser._find_ims_segments({}, source)

    def _extract_db2(self, source):
        return self.parser._find_db2_statements({}, source)

    def _security_scan(self, source):
        return self.rules.validate(source)

    def _generate_tokens(self, source):
        cics = self._extract_cics(source)
        return [self.parser._generate_token(c) for c in cics]

    def _calc_phi_c(self, source):
        v = len(self._security_scan(source))
        return max(0.0, 1.0 - (v * 0.1))

    def _export_ast(self, source):
        return self.parser.parse(source)

    def get_kernel_stats(self):
        return {
            "uptime": time.time() - self.start_time,
            "kernel_phi_c": self.kernel_phi_c,
            "substrate": "212-K",
            "memory": self.memory_manager.get_page_fault_stats(),
            "interrupts": self.interrupt_controller.get_interrupt_stats(),
            "syscalls": self.syscall_interface.get_syscall_stats(),
            "bus": self.bus.get_bus_stats()
        }
