import json
import os
import subprocess
import pandas as pd
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RSurvivalAnalyzer:
    def __init__(self, r_bin: str = "Rscript", r_lib: Optional[str] = None):
        self.r_bin = r_bin
        self.r_lib = r_lib

    def fit_coxme(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        fixed_effects: List[str],
        random_effects: Dict[str, List[str]],  # {group_var: [random_vars]}
        family: str = "gaussian",
        output_dir: str = "/tmp/r_coxme",
    ) -> Dict:
        """
        Ajusta modelo Cox com frailty complexo via pacote coxme do R.

        Args:
            df: DataFrame com dados
            duration_col: Coluna de tempo
            event_col: Coluna de evento (0/1)
            fixed_effects: Lista de covariáveis fixas
            random_effects: Dict {grupo: [variáveis aleatórias]}
            family: Família do modelo (gaussian, binomial, etc.)
            output_dir: Diretório para arquivos temporários

        Returns:
            Dict com resultados do modelo coxme
        """
        os.makedirs(output_dir, exist_ok=True)

        # Salvar dados como RDS
        data_path = os.path.join(output_dir, f"data_{hash(str(df.shape))}.rds")
        output_path = os.path.join(output_dir, f"result_{hash(str(df.shape))}.json")
        df_path = os.path.join(output_dir, f"data_{hash(str(df.shape))}.feather")
        df.to_feather(df_path)

        # Preparar fórmula de efeitos aleatórios
        re_terms = []
        for group_var, rand_vars in random_effects.items():
            if rand_vars:
                re_terms.append(f"({'+'.join(rand_vars)}|{group_var})")
            else:
                re_terms.append(f"(1|{group_var})")
        re_formula = " + ".join(re_terms)

        # Script R para coxme
        coxme_script = f"""
library(survival)
library(coxme)
library(broom)
library(jsonlite)

# Ler dados
data <- read_feather("{df_path}")

# Preparar fórmula
fe_formula <- as.formula(paste("Surv({duration_col}, {event_col}) ~",
                                paste(c({", ".join(f"'{x}'" for x in fixed_effects)}), collapse=" + ")))

# Ajustar modelo coxme
coxme_formula <- as.formula(paste(
    "Surv({duration_col}, {event_col}) ~",
    paste(c({", ".join(f"'{x}'" for x in fixed_effects)}), collapse=" + "),
    "+",
    "{re_formula}"
))

coxme_model <- coxme(coxme_formula, data=data)

# Extrair resultados tidos
fixed_tidy <- tidy(coxme_model, exponentiate=TRUE, conf.int=TRUE, effects="fixed")
random_tidy <- tidy(coxme_model, exponentiate=FALSE, conf.int=TRUE, effects="random")

# Variância dos efeitos aleatórios
variance_components <- as.data.frame(coxme_model$variance)

# Teste de proporcionalidade (para efeitos fixos)
ph_test <- cox.zph(coxme_model)

# Preparar output
output <- list(
    fixed_effects = fixed_tidy,
    random_effects = random_tidy,
    variance_components = variance_components,
    ph_test = list(
        global_p = ph_test$table["GLOBAL", "p"],
        by_var = lapply(rownames(ph_test$table)[-nrow(ph_test$table)], function(v) {{
            list(var=v, p=ph_test$table[v, "p"])
        }})
    ),
    concordance = coxme_model$concordance[1],
    aic = AIC(coxme_model),
    bic = BIC(coxme_model),
    n_groups = length(unique(data${list(random_effects.keys())[0] if random_effects else ''})),
    warnings = warnings()
)

# Salvar como JSON
write(toJSON(output, auto_unbox=TRUE, digits=10), "{output_path}")
"""

        script_path = os.path.join(output_dir, f"coxme_script_{hash(coxme_script)}.R")
        with open(script_path, 'w') as f:
            f.write(coxme_script)

        # Executar R
        env = os.environ.copy()
        if self.r_lib:
            env['R_LIBS'] = self.r_lib

        try:
            result = subprocess.run(
                [self.r_bin, "--vanilla", "--slave", "-f", script_path],
                capture_output=True, text=True, timeout=600,  # coxme pode ser lento
                env=env, cwd=output_dir
            )

            if result.returncode != 0:
                logger.error(f"Erro no R (coxme):\n{result.stderr}")
                raise RuntimeError(f"R coxme script failed: {result.stderr[:500]}")

            # Ler resultados
            with open(output_path, 'r') as f:
                r_results = json.load(f)

            # Converter para formato canônico
            return self._normalize_coxme_results(r_results, df, duration_col, event_col)

        finally:
            # Cleanup
            for f in [data_path, df_path, output_path, script_path]:
                if os.path.exists(f):
                    os.remove(f)

    def _normalize_coxme_results(
        self, r_results: Dict, df: pd.DataFrame, duration_col: str, event_col: str
    ) -> Dict:
        """Normaliza resultados do coxme para formato canônico."""
        # Fixed effects
        fixed_effects = {}
        for row in r_results.get('fixed_effects', []):
            var = row['term']
            fixed_effects[var] = {
                'coef': float(row['estimate']) if 'estimate' in row else None,
                'se': float(row['std.error']) if 'std.error' in row else None,
                'p': float(row['p.value']) if 'p.value' in row else None,
                'hr': float(row['estimate']) if 'estimate' in row else None,
                'ci_low': float(row['conf.low']) if 'conf.low' in row else None,
                'ci_high': float(row['conf.high']) if 'conf.high' in row else None,
            }

        # Random effects variance
        random_effects = {}
        for row in r_results.get('random_effects', []):
            group = row.get('group')
            if group:
                random_effects[group] = {
                    'variance': float(row.get('estimate', 0)),
                    'se': float(row.get('std.error', 0)),
                }

        # Variance components
        variance_components = {}
        vc_df = r_results.get('variance_components', {})
        if isinstance(vc_df, dict):
            for k, v in vc_df.items():
                variance_components[k] = float(v) if isinstance(v, (int, float)) else v

        return {
            'model_type': 'coxme',
            'fixed_effects': fixed_effects,
            'random_effects': random_effects,
            'variance_components': variance_components,
            'proportional_hazards': {
                'global_p': float(r_results.get('ph_test', {}).get('global_p', 1)),
                'by_variable': {
                    item['var']: float(item['p'])
                    for item in r_results.get('ph_test', {}).get('by_var', [])
                },
            },
            'concordance': float(r_results.get('concordance', 0)),
            'aic': float(r_results.get('aic', float('inf'))),
            'bic': float(r_results.get('bic', float('inf'))),
            'n_groups': int(r_results.get('n_groups', 0)),
            'r_warnings': r_results.get('warnings', []),
            'n_observations': len(df),
            'n_events': int(df[event_col].sum()),
        }
