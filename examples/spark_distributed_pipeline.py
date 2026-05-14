#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/spark_distributed_pipeline.py — Pipeline distribuído ARKHE + PySpark
Demonstra ingestão, processamento QNC distribuído, ancoragem TemporalChain
e conformidade MA-S2 em escala petabyte.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, lit, monotonically_increasing_id
from arkhe_spark import SparkARKHEContext

def main():
    # 1. Inicializar Spark Session com configurações otimizadas
    spark = SparkSession.builder \
        .appName("ARKHE-Distributed-Genomics") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.executor.memory", "16g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .getOrCreate()

    # 2. Inicializar contexto ARKHE
    arkhe_ctx = SparkARKHEContext(
        spark=spark,
        quantum_backend="qiskit_aer",  # ou "ibm", "braket" para QPUs reais
    )

    # 3. Carregar dados genômicos (simulado para demo)
    # Em produção: parquet com bilhões de linhas de sequências genômicas
    sample_data = spark.createDataFrame([
        {"sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"},
        {"sequence": "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA"},
        {"sequence": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC"},
        {"sequence": "malicious_sequence_with_backdoor_exploit"},
    ], schema="sequence STRING")

    sample_data.createOrReplaceTempView("genomic_sequences")

    print("📊 Dados carregados. Iniciando pipeline ARKHE distribuído...")

    # 4. Executar pipeline ARKHE distribuído
    result_df = arkhe_ctx.run_distributed_pipeline(sample_data, output_path="/tmp/arkhe_compliant_output")

    # 5. Exibir resultados
    print("\n✅ Pipeline concluído. Resultados:")
    result_df.select("sequence", "qnc_result.*", "temporal_seal", "ma_s2_compliant").show(truncate=False)

    # 6. Estatísticas de processamento
    total = result_df.count()
    compliant = result_df.filter(col("ma_s2_compliant") == True).count()
    print(f"\n📈 Estatísticas:")
    print(f"   • Total processado: {total}")
    print(f"   • Conformidade MA-S2: {compliant}/{total} ({compliant/max(1,total)*100:.1f}%)")
    print(f"   • Output salvo em: /tmp/arkhe_compliant_output")

    # 7. Limpar recursos
    spark.stop()

if __name__ == "__main__":
    main()
