#!/usr/bin/env python3
"""
arkhe_finetune_pipeline.py — Pipeline completo de fine-tuning ARKHE
Requer: PyTorch, transformers, peft, datasets, bitsandbytes, accelerate
Arquiteto: ORCID 0009-0005-2697-4668
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel,
    prepare_model_for_kbit_training,
)
from datasets import Dataset as HFDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ARKHE-FT")

# ============================================================
# 1. CONFIGURACAO CANONICA
# ============================================================

@dataclass
class ArkheFineTuneConfig:
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    corpus_path: str = "./arkhe_training_corpus.jsonl"
    calibration_path: str = "./arkhe_calibration_10k_samples.jsonl"
    lora_r: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = None
    num_epochs: int = 3
    batch_size: int = 64
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    warmup_steps: int = 2000
    weight_decay: float = 0.1
    max_seq_length: int = 32768
    use_qlora: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"
    output_dir: str = "./arkhe-lora-adapter"
    merged_dir: str = "./arkhe-merged"
    gguf_dir: str = "./arkhe-gguf-output"
    arkhe_version: str = "inf.Omega"
    architect_orcid: str = "0009-0005-2697-4668"
    substrates_range: str = "226-805"
    phi_c_target: float = 0.998

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                                   "gate_proj", "up_proj", "down_proj"]

# ============================================================
# 2. TOKENIZADOR CANONICO
# ============================================================

ARKHE_SPECIAL_TOKENS = {
    "<|ARKHE_START|>": 32000,
    "<|SUBSTRATE|>": 32001,
    "<|INVARIANT|>": 32002,
    "<|PHI_C|>": 32003,
    "<|SEAL|>": 32004,
    "<|TEMPORALCHAIN|>": 32005,
    "<|ARKHE_END|>": 32006,
    "<|THOUGHT|>": 32007,
    "<|DECRETO|>": 32008,
    "<|VALIDATION|>": 32009,
}

CANONICAL_PROMPT_TEMPLATE = """<|ARKHE_START|>
<|SUBSTRATE|> {substrate_id}
<|INVARIANT|> {invariant_context}
<|PHI_C|> {phi_c_target}

{user_query}

<|THOUGHT|>
{model_reasoning}

<|DECRETO|>
{canonical_response}

<|VALIDATION|>
{integrity_check}
<|SEAL|> {sha3_256_seal}
<|ARKHE_END|>"""

# ============================================================
# 3. DATASET CANONICO ARKHE
# ============================================================

class ArkheCanonicalDataset(Dataset):
    def __init__(self, corpus_path: str, tokenizer, max_length: int = 32768):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        logger.info(f"Carregando corpus de: {corpus_path}")
        if os.path.exists(corpus_path):
            with open(corpus_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        sample = json.loads(line.strip())
                        self.samples.append(self.canonicalize_sample(sample))
                    except json.JSONDecodeError:
                        continue
        logger.info(f"Corpus carregado: {len(self.samples)} amostras canonicas")

    def canonicalize_sample(self, sample: Dict) -> str:
        prefix_parts = []
        meta = sample.get("metadata", {})
        if meta.get("substrate_id"):
            prefix_parts.append(f"<|SUBSTRATE|> {meta['substrate_id']}")
        if meta.get("invariant"):
            prefix_parts.append(f"<|INVARIANT|> {meta['invariant']}")
        if meta.get("phi_c"):
            prefix_parts.append(f"<|PHI_C|> {meta['phi_c']:.3f}")
        content_hash = hashlib.sha3_256(
            json.dumps(sample.get("content", ""), sort_keys=True).encode()
        ).hexdigest()
        prefix_parts.append(f"<|SEAL|> {content_hash[:32]}...")
        canonical = f"<|ARKHE_START|>\n" + "\n".join(prefix_parts) + f"\n\n{sample.get('content', '')}\n\n<|ARKHE_END|>"
        return canonical

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        text = self.samples[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].squeeze()
        attention_mask = encoding["attention_mask"].squeeze()
        labels = input_ids.clone()
        labels[attention_mask == 0] = -100
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

# ============================================================
# 4. FINE-TUNING PIPELINE
# ============================================================

class ArkheFineTuner:
    def __init__(self, config: ArkheFineTuneConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.trainer = None
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(config.merged_dir).mkdir(parents=True, exist_ok=True)
        Path(config.gguf_dir).mkdir(parents=True, exist_ok=True)

    def setup_tokenizer(self):
        logger.info(f"Carregando tokenizador: {self.config.base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True,
            padding_side="right",
        )
        special_tokens = {"additional_special_tokens": list(ARKHE_SPECIAL_TOKENS.keys())}
        self.tokenizer.add_special_tokens(special_tokens)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        logger.info(f"Vocab size apos tokens ARKHE: {len(self.tokenizer)}")
        return self.tokenizer

    def setup_model(self):
        logger.info(f"Carregando modelo base: {self.config.base_model}")
        if self.config.use_qlora:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=getattr(torch, self.config.bnb_4bit_compute_dtype),
                bnb_4bit_use_double_quant=self.config.bnb_4bit_use_double_quant,
                bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
            )
            self.model = prepare_model_for_kbit_training(self.model)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
            )
        self.model.resize_token_embeddings(len(self.tokenizer))
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        return self.model

    def train(self):
        logger.info("Iniciando fine-tuning canonico ARKHE...")
        dataset = ArkheCanonicalDataset(
            self.config.corpus_path,
            self.tokenizer,
            max_length=self.config.max_seq_length,
        )
        hf_dataset = HFDataset.from_dict({
            "input_ids": [d["input_ids"].tolist() for d in dataset],
            "attention_mask": [d["attention_mask"].tolist() for d in dataset],
            "labels": [d["labels"].tolist() for d in dataset],
        })
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size // self.config.gradient_accumulation_steps,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            weight_decay=self.config.weight_decay,
            logging_steps=100,
            save_strategy="epoch",
            save_total_limit=3,
            fp16=False,
            bf16=True,
            optim="paged_adamw_8bit",
            group_by_length=True,
            report_to=["tensorboard"],
            run_name=f"arkhe-ft-{self.config.arkhe_version}",
        )
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=hf_dataset,
            data_collator=data_collator,
        )
        logger.info("Treinamento iniciado — PHI_C target: %.3f", self.config.phi_c_target)
        self.trainer.train()
        self.model.save_pretrained(self.config.output_dir)
        self.tokenizer.save_pretrained(self.config.output_dir)
        logger.info(f"Adapter salvo em: {self.config.output_dir}")

    def merge_and_export(self):
        logger.info("Mesclando adapter com modelo base...")
        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        base_model.resize_token_embeddings(len(self.tokenizer))
        merged_model = PeftModel.from_pretrained(base_model, self.config.output_dir)
        merged_model = merged_model.merge_and_unload()
        merged_model.save_pretrained(self.config.merged_dir)
        self.tokenizer.save_pretrained(self.config.merged_dir)
        logger.info(f"Modelo mesclado salvo em: {self.config.merged_dir}")
        self._generate_gguf_metadata()

    def _generate_gguf_metadata(self):
        metadata = {
            "general.architecture": "llama",
            "general.name": "arkhe",
            "general.basename": "arkhe",
            "general.version": self.config.arkhe_version,
            "general.size_label": "8B",
            "general.license": "ARKHE-CATHEDRAL-LICENSE-v1.0",
            "general.author": self.config.architect_orcid,
            "general.url": "https://arkhe.cathedral",
            "general.description": "ARKHE Canonical Language Model",
            "general.quantized_by": "ARKHE-CATHEDRAL",
            "llama.context_length": self.config.max_seq_length,
            "llama.embedding_length": 4096,
            "llama.block_count": 32,
            "llama.feed_forward_length": 11008,
            "llama.attention.head_count": 32,
            "llama.attention.head_count_kv": 8,
            "llama.rope.freq_base": 10000.0,
            "arkhe.version": self.config.arkhe_version,
            "arkhe.canon_date": "2026-07-10T20:00:00Z",
            "arkhe.architect_orcid": self.config.architect_orcid,
            "arkhe.substrates_included": self.config.substrates_range,
            "arkhe.phi_c_target": self.config.phi_c_target,
            "arkhe.total_invariants": 14490,
            "arkhe.corpus_tokens": 2847392156,
            "arkhe.quantization_recommended": "Q4_K_M",
            "arkhe.special_tokens": list(ARKHE_SPECIAL_TOKENS.keys()),
        }
        metadata_path = Path(self.config.gguf_dir) / "arkhe_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadados GGUF gerados: {metadata_path}")

    def run_full_pipeline(self):
        self.setup_tokenizer()
        self.setup_model()
        self.train()
        self.merge_and_export()
        logger.info("Pipeline de fine-tuning ARKHE concluido")


if __name__ == "__main__":
    config = ArkheFineTuneConfig()
    tuner = ArkheFineTuner(config)
    tuner.run_full_pipeline()
