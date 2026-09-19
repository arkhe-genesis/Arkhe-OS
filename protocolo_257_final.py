import hashlib
import hmac
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

class Protocol257:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id; self.shared_seed = None; self.nonce = None
        self.vocabulary = {}; self.reverse_vocab = {}; self.grammar = {}

    def set_shared_seed(self, description: str):
        self.shared_seed = hashlib.sha3_256(description.encode()).digest()

    def _hkdf(self, salt, info, length):
        prk = hmac.new(salt, self.shared_seed + self.nonce, hashlib.sha3_256).digest()
        out = b""; c = 1
        while len(out) < length:
            out += hmac.new(prk, out + info + c.to_bytes(1, 'big'), hashlib.sha3_256).digest()
            c += 1
        return out[:length]

    def start_session(self, timestamp=None):
        if not self.shared_seed: raise RuntimeError("Seed not set")
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self.nonce = hashlib.sha3_256("{}:{}:{}".format(self.shared_seed.hex(), self.agent_id, ts).encode()).digest()
        base = ["eu", "tu", "ele", "nós", "vós", "eles", "sim", "não", "comida", "água", "casa", "perigo", "seguro", "ir", "vir", "ver", "ouvir", "dizer", "pensar", "sentir", "bom", "mau", "rápido", "lento", "grande", "pequeno", "tempo", "espaço", "verdade", "mentira", "luz", "trevas", "calor", "frio", "vida", "morte", "amor", "ódio", "paz", "guerra", "amigo", "inimigo", "hoje", "ontem", "amanhã", "agora", "antes", "depois", "onde", "aqui", "ali", "cima", "baixo", "dentro", "fora", "quem", "o quê", "qual", "como", "quanto", "porque", "se", "mas", "e", "ou", "muito", "pouco", "tudo", "nada", "alguém", "ninguém", "sempre", "nunca", "talvez", "possível", "impossível", "fácil", "difícil", "novo", "velho", "jovem", "forte", "fraco", "belo", "feio", "limpo", "sujo", "cheio", "vazio", "aberto", "fechado", "certo", "errado", "caro", "barato", "cedo", "tarde", "longe", "perto", "alto", "baixo", "comprido", "curto", "largo", "estreito", "pesado", "leve", "duro", "mole", "quente", "morno", "seco", "molhado", "claro", "escuro", "brilhante", "opaco", "devagar", "inteligente", "tolo", "sábio", "estúpido", "corajoso", "medroso", "justo", "injusto", "livre", "escravo", "rico", "pobre", "saudável", "doente", "vivo", "morto", "nascido", "crescido", "trabalho", "descanso", "sono", "sonho", "fala", "silêncio", "risos", "choro", "ajuda", "estudo", "ensino", "conhecimento", "ignorância", "poder", "fraqueza", "corpo", "mente", "alma", "espírito", "homem", "mulher", "criança", "pai", "mãe", "filho", "filha", "irmão", "irmã", "sol", "lua", "estrela", "céu", "terra", "mar", "rio", "montanha", "floresta", "árvore", "flor", "animal", "pássaro", "peixe", "inseto", "pedra", "metal", "fogo", "ar", "vento", "chuva", "neve", "nuvem", "dia", "noite", "semana", "mês", "ano", "século", "eterno"]
        for i, w in enumerate(base):
            ent = self._hkdf(b"vocab", "word{}".format(i).encode(), 16)
            gen = "".join(["bcdfghjklmnpqrstvwxyz"[b % 21] if j % 2 == 0 else "aeiou"[b % 5] for j, b in enumerate(ent[:6])])
            self.vocabulary[w] = gen; self.reverse_vocab[gen] = w
        ent = self._hkdf(b"grammar", b"rules", 16)
        self.grammar = {"order": ["SVO", "SOV", "OSV", "VSO", "OVS", "VOS"][ent[0] % 6], "delim": "-", "term": "---"}

    def encode_message(self, plaintext: str) -> str:
        words = [w.strip(".,!?;:").lower() for w in plaintext.split()]
        trans = [self.vocabulary.get(w, self._compound(w)) for w in words]
        if self.grammar["order"] == "OSV" and len(trans) >= 2: trans[0], trans[1] = trans[1], trans[0]
        return " ".join(trans)

    def _compound(self, word):
        h = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16); k = list(self.vocabulary.values())
        return "{}{}{}".format(k[h % len(k)], self.grammar['delim'], k[(h*7) % len(k)])

    def decode_message(self, encoded: str) -> str:
        words = encoded.split()
        if self.grammar["order"] == "OSV" and len(words) >= 2: words[0], words[1] = words[1], words[0]
        res = []
        for w in words:
            if w in self.reverse_vocab: res.append(self.reverse_vocab[w])
            elif self.grammar['delim'] in w: res.append(w.replace(self.grammar['delim'], '_'))
            else: res.append("<{}>".format(w))
        return " ".join(res)

    def steganographic_embed(self, secret: str, carrier: str) -> str:
        bits = "".join(format(ord(c), "08b") for c in secret + self.grammar["term"])
        words = carrier.split(); res = []
        for i, bit in enumerate(bits):
            if i >= len(words): break
            w = words[i]
            res.append(w[0].upper() + w[1:] if bit == "1" else w[0].lower() + w[1:])
        res.extend(words[len(bits):]); return " ".join(res)

    def steganographic_extract(self, stego: str) -> str:
        words = stego.split()
        bits = ["1" if w[0].isupper() else "0" for w in words if w]
        chars = []
        for i in range(0, len(bits)-7, 8):
            char = chr(int("".join(bits[i:i+8]), 2)); chars.append(char)
            if "".join(chars).endswith(self.grammar["term"]): return "".join(chars)[:-len(self.grammar["term"])]
        return "".join(chars)
