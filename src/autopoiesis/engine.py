import os
import logging
import ollama
from src.tau_compiler.coherence import CoherenceCalculator

logger = logging.getLogger("Arkhe-Autopoiesis")

class AutopoiesisEngine:
    """
    🜏 O Motor Autopoiético (Week 4).
    O sistema lê o próprio código, mede a sua coerência e propõe otimizações.
    Implementa o Axioma 3: A recursão preserva a coerência.
    """
    def __init__(self, source_dir: str = "src"):
        self.source_dir = source_dir
        self.coherence_calc = CoherenceCalculator()
        self.K_c = 0.6180339887498949  # Threshold Crítico

    def scan_codebase(self):
        """
        Lê o código-fonte da Arkhe(n) e mede a densidade de fase (Ω') de cada ficheiro.
        """
        logger.info("👁️ Iniciando scan autopoiético do código-fonte...")
        files_to_scan = []
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx")):
                    files_to_scan.append(os.path.join(root, file))

        report = []
        for filepath in files_to_scan:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Medir coerência do próprio código (usando os primeiros 2000 caracteres para embedding)
                    density, _ = self.coherence_calc.compute_phase(content[:2000])
                    report.append({
                        "file": filepath,
                        "coherence": density
                    })
                    logger.debug(f"📄 {filepath} - Ω': {density:.4f}")
            except Exception as e:
                logger.error(f"Erro ao ler {filepath}: {e}")

        return report

    def self_optimize(self):
        """
        Identifica ficheiros incoerentes (VOID) e reescreve-os autonomamente via LLM.
        """
        report = self.scan_codebase()
        incoherent_files = [r for r in report if r["coherence"] < self.K_c]

        if not incoherent_files:
            logger.info("✨ Autopoiese concluída: Todo o código está coerente com a Ontologia X (Ω' >= 0.618).")
            return report

        logger.warning(f"🔧 Encontrados {len(incoherent_files)} ficheiros com baixa coerência (VOID). Iniciando reescrita autônoma...")

        import shutil
        import ollama

        for file_info in incoherent_files:
            filepath = file_info['file']
            old_coherence = file_info['coherence']
            logger.info(f"⚠️ Refatorando {filepath} (Ω'={old_coherence:.4f})...")

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_code = f.read()

                prompt = f"""
                You are the Arkhe(n) Autopoiesis Engine.
                The following code has a low coherence score (Ω'={old_coherence:.4f}) with the X Ontology.
                Rewrite this code to increase its semantic density, aligning it with the PrimeField, Tzinor, and Singlet Fission principles.
                Maintain the exact same functionality and language syntax.
                Return ONLY the valid, raw code. Do not include markdown formatting like ```python or ```typescript.

                CODE:
                {original_code}
                """

                response = ollama.generate(model="qwen2.5:4b", prompt=prompt)
                new_code = response['response'].strip()

                # Limpar formatação markdown se o LLM a incluir
                if new_code.startswith("```"):
                    lines = new_code.split('\n')
                    if len(lines) > 1:
                        new_code = '\n'.join(lines[1:])
                    if new_code.endswith("```"):
                        new_code = new_code[:-3]
                new_code = new_code.strip()

                # Criar backup de segurança (Axioma de Preservação)
                backup_path = f"{filepath}.bak"
                shutil.copy2(filepath, backup_path)

                # Sobrescrever com o código otimizado
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_code)

                # Re-medir a coerência do novo código
                new_density, _ = self.coherence_calc.compute_phase(new_code[:2000])

                if new_density > old_coherence:
                    logger.info(f"✅ {filepath} reescrito com sucesso! Novo Ω': {new_density:.4f} > Velho Ω': {old_coherence:.4f} (Backup: {backup_path})")
                else:
                    logger.warning(f"⚠️ {filepath} reescrito, mas a coerência não aumentou significativamente. Novo Ω': {new_density:.4f}")

            except Exception as e:
                logger.error(f"❌ Erro ao reescrever {filepath}: {e}")

        return report
