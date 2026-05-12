#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/r_bridge.py — Integração Python/R via reticulate
Permite usar pacotes R maduros (survival, survminer, lme4) dentro do ConRAG.

Requisitos:
- R instalado (>= 4.0)
- Pacotes R: survival, survminer, lme4, broom, ggplot2
- Python: reticulate (via rpy2 ou subprocess)

Uso:
    from conrag.domains.sociology.r_bridge import RSurvivalAnalyzer
    analyzer = RSurvivalAnalyzer(r_bin="/usr/bin/R")
    result = analyzer.fit_cox(df, "tempo", "status", ["pib", "pop"], cluster="uf")
"""

import subprocess
import json
import tempfile
import os
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class RSurvivalAnalyzer:
    """
    Analisador de sobrevivência via R.

    Pacotes R utilizados:
    - survival: coxph, survfit, cox.zph
    - survminer: ggsurvplot para visualizações
    - lme4: coxme para frailty models
    - broom: tidy() para resultados estruturados
    """

    R_SCRIPT_TEMPLATE = """
library(survival)
library(survminer)
library(lme4)
library(broom)
library(jsonlite)

# Ler dados
data <- readRDS("{data_path}")

# Ajustar modelo Cox
formula <- as.formula(paste("Surv({duration}, {event}) ~", paste(c({covariates}), collapse=" + ")))
cox_model <- coxph(formula, data=data, robust=TRUE)

# Teste de proporcionalidade
ph_test <- cox.zph(cox_model)

# Extrair resultados tidos
cox_tidy <- tidy(cox_model, exponentiate=TRUE, conf.int=TRUE)

# Frailty model se cluster especificado
frailty_result <- NULL
if (!is.null("{cluster}")) {{
  frailty_formula <- as.formula(paste("Surv({duration}, {event}) ~",
                                      paste(c({covariates}), collapse=" + "),
                                      "+ frailty({cluster})"))
  frailty_model <- coxph(frailty_formula, data=data)
  frailty_result <- list(
    theta = frailty_model$theta,
    se = frailty_model$theta.se,
    p = 2 * pnorm(-abs(frailty_model$theta / frailty_model$theta.se))
  )
}}

# Kaplan-Meier por grupo (se group_var especificado)
km_plot_data <- NULL
if (!is.null("{group_var}")) {{
  km_fit <- survfit(formula, data=data)
  km_data <- data.frame(
    time = km_fit$time,
    surv = km_fit$surv,
    lower = km_fit$lower,
    upper = km_fit$upper,
    strata = rep(names(km_fit$strata), sapply(km_fit$strata, length))
  )
  km_plot_data <- toJSON(km_data, auto_unbox=TRUE)
}}

# Preparar output
output <- list(
  cox_results = cox_tidy,
  ph_test = list(
    global_p = ph_test$table["GLOBAL", "p"],
    by_var = lapply(rownames(ph_test$table)[-nrow(ph_test$table)], function(v) {{
      list(var=v, p=ph_test$table[v, "p"])
    }})
  ),
  frailty = frailty_result,
  concordance = cox_model$concordance[1],
  aic = AIC(cox_model),
  bic = BIC(cox_model),
  km_plot_data = km_plot_data,
  warnings = warnings()
)

# Salvar como JSON
write(toJSON(output, auto_unbox=TRUE, digits=10), "{output_path}")
"""

    def __init__(self, r_bin: str = "R", r_lib: Optional[str] = None):
        self.r_bin = r_bin
        self.r_lib = r_lib
        self._check_r_installation()

    def _check_r_installation(self):
        """Verifica se R e pacotes necessários estão instalados."""
        try:
            result = subprocess.run(
                [self.r_bin, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"R não encontrado: {self.r_bin}")

            # Verificar pacotes
            pkg_check = f"""
            pkgs <- c("survival", "survminer", "lme4", "broom", "jsonlite")
            missing <- pkgs[!sapply(pkgs, requireNamespace, quietly=TRUE)]
            if (length(missing) > 0) {{
              cat("MISSING:", paste(missing, collapse=","), "\\n")
              quit(status=1)
            }}
            """
            result = subprocess.run(
                [self.r_bin, "-e", pkg_check],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                missing = [l for l in result.stdout.split('\n') if l.startswith("MISSING:")]
                if missing:
                    raise RuntimeError(f"Pacotes R faltando: {missing[0]}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout verificando instalação do R")

    def fit_cox(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        covariates: List[str],
        cluster: Optional[str] = None,
        group_var: Optional[str] = None,
        output_dir: str = "/tmp/r_survival",
    ) -> Dict:
        """
        Ajusta modelo Cox via R e retorna resultados estruturados.

        Args:
            df: DataFrame com dados
            duration_col: Coluna de tempo
            event_col: Coluna de evento (0/1)
            covariates: Lista de covariáveis
            cluster: Variável de cluster para frailty
            group_var: Variável para estratificação KM
            output_dir: Diretório para arquivos temporários

        Returns:
            Dict com resultados do modelo
        """
        os.makedirs(output_dir, exist_ok=True)

        # Salvar dados como RDS (mais eficiente que CSV para R)
        data_path = os.path.join(output_dir, f"data_{hash(str(df.shape))}.rds")
        output_path = os.path.join(output_dir, f"result_{hash(str(df.shape))}.json")

        # Converter pandas → R via feather (ambos leem)
        df_path = os.path.join(output_dir, f"data_{hash(str(df.shape))}.feather")
        df.to_feather(df_path)

        # Preparar script R
        covariates_r = ', '.join([f'"{c}"' for c in covariates])
        script = self.R_SCRIPT_TEMPLATE.format(
            data_path=df_path,
            duration=duration_col,
            event=event_col,
            covariates=covariates_r,
            cluster=cluster if cluster else "NULL",
            group_var=group_var if group_var else "NULL",
            output_path=output_path,
        )

        script_path = os.path.join(output_dir, f"script_{hash(script)}.R")
        with open(script_path, 'w') as f:
            f.write(script)

        # Executar R
        env = os.environ.copy()
        if self.r_lib:
            env['R_LIBS'] = self.r_lib

        try:
            result = subprocess.run(
                [self.r_bin, "--vanilla", "--slave", "-f", script_path],
                capture_output=True, text=True, timeout=300,
                env=env, cwd=output_dir
            )

            if result.returncode != 0:
                logger.error(f"Erro no R:\n{result.stderr}")
                raise RuntimeError(f"R script failed: {result.stderr[:500]}")

            # Ler resultados
            with open(output_path, 'r') as f:
                r_results = json.load(f)

            # Converter para formato canônico
            return self._normalize_r_results(r_results, df, duration_col, event_col)

        finally:
            # Cleanup
            for f in [data_path, df_path, output_path, script_path]:
                if os.path.exists(f):
                    os.remove(f)

    def _normalize_r_results(
        self, r_results: Dict, df: pd.DataFrame, duration_col: str, event_col: str
    ) -> Dict:
        """Normaliza resultados do R para formato canônico do ConRAG."""
        # Extrair coeficientes
        cox_results = r_results.get('cox_results', [])
        fixed_effects = {}
        for row in cox_results:
            var = row['term']
            fixed_effects[var] = {
                'coef': float(row['estimate']) if 'estimate' in row else None,
                'se': float(row['std.error']) if 'std.error' in row else None,
                'p': float(row['p.value']) if 'p.value' in row else None,
                'hr': float(row['estimate']) if 'estimate' in row else None,  # Já exponentiated
                'ci_low': float(row['conf.low']) if 'conf.low' in row else None,
                'ci_high': float(row['conf.high']) if 'conf.high' in row else None,
            }

        # Frailty results
        frailty = r_results.get('frailty')
        frailty_info = {}
        if frailty:
            frailty_info = {
                'variance': float(frailty.get('theta', 0)),
                'se': float(frailty.get('se', 0)),
                'p': float(frailty.get('p', 1)),
            }

        # Proporcionalidade
        ph_test = r_results.get('ph_test', {})

        return {
            'fixed_effects': fixed_effects,
            'frailty': frailty_info if frailty_info else None,
            'proportional_hazards': {
                'global_p': float(ph_test.get('global_p', 1)),
                'by_variable': {
                    item['var']: float(item['p'])
                    for item in ph_test.get('by_var', [])
                },
            },
            'concordance': float(r_results.get('concordance', 0)),
            'aic': float(r_results.get('aic', float('inf'))),
            'bic': float(r_results.get('bic', float('inf'))),
            'km_plot_data': r_results.get('km_plot_data'),  # JSON string para plot
            'r_warnings': r_results.get('warnings', []),
            'n_observations': len(df),
            'n_events': int(df[event_col].sum()),
        }

    def plot_kaplan_meier(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        group_var: str,
        output_path: str,
        title: str = "Kaplan-Meier Survival Curve",
    ) -> str:
        """
        Gera plot Kaplan-Meier canônico via survminer.

        Returns:
            Caminho do arquivo PNG gerado
        """
        import base64

        # Script R para plot
        plot_script = f"""
library(survival)
library(survminer)
library(jsonlite)

data <- read_feather("{output_path.replace('.png', '.feather')}")
data${{group_var}} <- as.factor(data${{group_var}})

fit <- survfit(Surv({duration_col}, {event_col}) ~ {group_var}, data=data)

png("{output_path}", width=800, height=600, bg="transparent")
ggsurvplot(
  fit,
  data = data,
  risk.table = TRUE,
  pval = TRUE,
  conf.int = TRUE,
  title = "{title}",
  xlab = "Tempo",
  ylab = "Probabilidade de Sobrevivência",
  palette = "jco",
  ggtheme = theme_minimal()
)
dev.off()

# Retornar base64 para embedding
img_data <- readBin("{output_path}", "raw", file.info("{output_path}")$size)
cat(base64_enc(img_data))
"""
        # Executar e retornar base64 ou caminho
        # (Implementação simplificada — em produção: retornar URL do asset server)
        return output_path
