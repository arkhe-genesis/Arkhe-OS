# ARKHE OS — SUBSTRATO 253: OWL ONTOLOGY PARSER
## Guia de Implantação e Parsing

### Passo 1: Configurar Parser de Ontologias

```bash
# Instalar dependências para parsing RDF/OWL
$ npm install n3 owl-reasoner-lite @arkhe-os/parser

# Configurar reasoner (opcional, para verificação de consistência)
$ cat > owl-reasoner-config.json << 'EOF'
{
  "reasoner": "hermite",
  "timeout_ms": 30000,
  "max_memory_mb": 2048,
  "cache_inferences": true
}
EOF

# Registrar frontend no PolymathParser
$ node -e "
const { PolymathParser } = require('@arkhe-os/parser');
const { OWLFrontend } = require('./owl_frontend');
const parser = new PolymathParser();
parser.registerFrontend(new OWLFrontend({
  reasonerConfig: require('./owl-reasoner-config.json')
}));
console.log('✅ OWL frontend registered');
"
```

### Passo 2: Parse e Validação de Ontologia

```bash
# Parse de ontologia em Turtle
$ arkhe ontology parse \
  --file ./ontologies/biomedical.ttl \
  --output ./lfir/biomedical.json \
  --reason \
  --verbose

🦉 OWL Parser Output:
• Ontology IRI: http://example.org/biomedical#
• Classes extracted: 247
• Properties extracted: 89 (62 object, 27 datatype)
• Individuals extracted: 1,342
• Axioms processed: 892
• Reasoning: ✅ Consistent (0.847s)
• Inferred subClassOf: +34
• Coherence Score: Φ_C = 0.873
• LFIR exported: ./lfir/biomedical.json

# Verificar coerência detalhada
$ arkhe ontology coherence --file ./ontologies/biomedical.ttl --report

📊 Coherence Report for biomedical.ttl:
┌─────────────────────┬─────────┬─────────┐
│ Component           │ Score   │ Weight  │
├─────────────────────┼─────────┼─────────┤
│ Consistency         │ 1.000   │ 0.40    │
│ Completeness        │ 0.892   │ 0.30    │
│ Reuse (external)    │ 0.764   │ 0.20    │
│ Documentation       │ 0.931   │ 0.10    │
├─────────────────────┼─────────┼─────────┤
│ Φ_C (weighted)      │ 0.873   │ 1.00    │
└─────────────────────┴─────────┴─────────┘

💡 Recommendations:
• Add rdfs:comment to 12 classes without documentation
• Consider defining equivalentClass for 27 undefined classes
• Reuse SKOS for 8 local properties to improve interoperability
```

### Passo 3: Comparação e Alinhamento de Ontologias

```bash
# Comparar duas versões de ontologia
$ arkhe ontology diff \
  --file1 ./ontologies/biomedical_v1.ttl \
  --file2 ./ontologies/biomedical_v2.ttl \
  --output ./reports/ontology_diff.json

🔍 Ontology Diff Report:
• Semantic distance: d = 0.142 (low drift)
• Classes added: 12
• Classes removed: 3
• Properties modified: 7
• Axioms changed: 34
• Coherence change: Φ_C: 0.873 → 0.891 (+0.018)

📈 Impact Analysis:
• New class "GenomicVariant" improves completeness (+0.03)
• Added disjointWith between "Protein" and "NucleicAcid" (+0.02)
• Removed inconsistent axiom in "MetabolicProcess" (+0.05)

# Alinhar ontologias para integração
$ arkhe ontology align \
  --source ./ontologies/biomedical.ttl \
  --target ./ontologies/clinical.ttl \
  --threshold 0.75 \
  --output ./alignments/bio-clinical.json

🔗 Alignment Results:
• Class mappings found: 89 (above threshold 0.75)
• Property mappings: 34
• Confidence avg: 0.84
• Suggested merges: 12
• Exported to: ./alignments/bio-clinical.json
```

### Passo 4: Integração com Zinc+ para Prova de Consistência

(Verifique as lógicas implementadas em `owl_reasoning_integration.ts`).
