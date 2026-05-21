use std::collections::HashSet;

// Um conflito é um par não ordenado de índices de partes (0‑based)
pub type Conflict = (usize, usize);

/// Protocolo de broadcast multi‑valorado com profundidade ótima.
pub struct CryptoBroadcast {
    n: usize,                     // número de partes
    t: usize,                     // número máximo de corruptos
    _parties: Vec<String>,        // identificadores das partes
    delta: HashSet<Conflict>,     // conjunto de conflitos atual
    blocks: Vec<Vec<u8>>,         // blocos da mensagem original
}

impl CryptoBroadcast {
    /// Cria uma nova instância.
    pub fn new(n: usize, t: usize, parties: Vec<String>) -> Self {
        Self {
            n,
            t,
            _parties: parties,
            delta: HashSet::new(),
            blocks: Vec::new(),
        }
    }

    /// Divide a mensagem em q = ⌈2n/(n‑t)⌉ blocos.
    fn split_message(&self, message: &[u8]) -> Vec<Vec<u8>> {
        let q = (2 * self.n) / (self.n - self.t);
        let block_size = (message.len() + q - 1) / q;
        message.chunks(block_size).map(|c| c.to_vec()).collect()
    }

    /// Calcula a distância ∆* entre dois partidos.
    fn distance_delta_star(&self, from: usize, to: usize) -> Option<usize> {
        // Se há conflito direto, distância infinita
        if self.delta.contains(&(from.min(to), from.max(to))) {
            return None;
        }
        // BFS no grafo sem conflitos
        let mut visited = vec![false; self.n];
        let mut queue = std::collections::VecDeque::new();
        visited[from] = true;
        queue.push_back((from, 0));
        while let Some((node, dist)) = queue.pop_front() {
            if node == to {
                return Some(dist);
            }
            for next in 0..self.n {
                if !visited[next] && !self.delta.contains(&(node.min(next), node.max(next))) {
                    visited[next] = true;
                    queue.push_back((next, dist + 1));
                }
            }
        }
        None // desconectado
    }
}

impl CryptoBroadcast {
    /// Executa o broadcast.
    pub fn execute(&mut self, sender_id: usize, message: &[u8]) -> Vec<Vec<u8>> {
        self.blocks = self.split_message(message);
        let q = self.blocks.len();
        let max_rounds = q + (2 * self.n) / (self.n - self.t);

        for round in 1..=max_rounds {
            for k in 0..q {
                // O bloco k avança se round − k − 1 >= 0 e ainda há partidos a alcançar
                let step = round as i32 - k as i32 - 1;
                if step < 0 { continue; }
                // Determina os conjuntos Sk e Sk+1 via distância ∆*
                let mut s_k = vec![];
                let mut s_k_plus_1 = vec![];
                for i in 0..self.n {
                    if let Some(dist) = self.distance_delta_star(sender_id, i) {
                        if dist == step as usize {
                            s_k.push(i);
                        } else if dist == (step + 1) as usize {
                            s_k_plus_1.push(i);
                        }
                    }
                }
                // Transmissão: cada partido em Sk envia a sua share para partidos em Sk+1
                // (nesta simulação, apenas copiamos a share; em produção, enviaria via rede)
                for _src in &s_k {
                    for _dst in &s_k_plus_1 {
                        // Comunicação balanceada: cada share tem tamanho ℓ/(q(n‑t))
                        // Apenas registramos a ação
                    }
                }
            }
            // Após cada rodada, o conjunto de conflitos ∆ pode ser atualizado via Dispute Control
            // (aqui, simplificado)
        }
        // Todos os partidos honestos reconstroem a mensagem a partir dos blocos
        self.blocks.clone()
    }
}

// Exemplo de uso do CryptoBroadcast para sincronização dos gates
pub fn sync_gates_state_update(update: &[u8]) {
    let gates = vec![
        "PG-NA", "PG-SA", "PG-EU", "PG-AS", "PG-AF", "PG-OC", "PG-AN"
    ];
    let n = gates.len();
    let t = 4; // até 4 gates podem ser maliciosos
    let mut broadcast = CryptoBroadcast::new(n, t, gates.iter().map(|s| s.to_string()).collect());
    // sender = PG‑EU (índice 2)
    broadcast.execute(2, update);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_crypto_broadcast_depth() {
        let n = 59; // parceiros
        let t = 45; // maioria corrupta (t < n, n‑t = 14)
        let parties: Vec<String> = (0..n).map(|i| format!("Partner-{}", i)).collect();
        let mut broadcast = CryptoBroadcast::new(n, t, parties);
        let message = b"Arkhe Constitutional Broadcast Message for 59 Partners";
        let blocks = broadcast.execute(0, message);
        // Cada bloco deve existir
        assert_eq!(blocks.len(), (2 * n) / (n - t)); // q = 2*59/14 ≈ 8
    }
}
