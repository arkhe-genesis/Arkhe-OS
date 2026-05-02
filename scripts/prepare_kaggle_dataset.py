# scripts/prepare_kaggle_dataset.py
"""Prepare AME2020 + OctoSpec dataset for Kaggle publication."""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Ensure train_tabula_ame2020 can be imported
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def prepare_kaggle_dataset(output_dir: str = 'kaggle/arkhe-nuclear-coherence'):
    """Create Kaggle-ready dataset with documentation."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load or generate data
    from train_tabula_ame2020 import AME2020TabulaTrainer
    trainer = AME2020TabulaTrainer()
    df = trainer.download_ame2020()

    # Add engineered features
    df_engineered = trainer.engineer_features(df)

    # Create metadata
    dataset_info = {
        'title': 'ARKHE Nuclear Coherence Dataset',
        'subtitle': 'Octonionic Anomaly Index predictions from AME2020 nuclear properties',
        'description': '''
This dataset contains nuclear properties from AME2020 augmented with the
Octonionic Anomaly Index (IAO) — a synthetic target representing CAPTURE-like
coherence in quantum oscillator systems.

## Features
- Basic: Z, N, A (proton/neutron/mass numbers)
- Energetic: BindingEnergy_MeV_per_nucleon, MassExcess_keV
- Temporal: HalfLife_seconds
- Derived: Asymmetry, Z_over_A, log-transforms, shell effects
- Target: OctonionicAnomalyIndex (0-1, lower = more coherent)

## Use Cases
1. Train models to predict nuclear coherence regimes
2. Explore correlations between nuclear structure and octonionic geometry
3. Benchmark XGBoost, neural networks, or symbolic regression

## Citation
If you use this dataset, please cite:
```
@dataset{oliveira2026arkhe,
  title = {ARKHE Nuclear Coherence Dataset},
  author = {Oliveira, Rafael},
  year = {2026},
  publisher = {Kaggle},
  url = {https://kaggle.com/datasets/arkhe-os/nuclear-coherence}
}
```
        '''.strip(),
        'license': 'CC0-1.0',
        'columns': {
            'Z': 'Proton number',
            'N': 'Neutron number',
            'A': 'Mass number (Z+N)',
            'BindingEnergy_MeV_per_nucleon': 'Binding energy per nucleon (MeV)',
            'HalfLife_seconds': 'Half-life in seconds',
            'MassExcess_keV': 'Mass excess in keV',
            'OctonionicAnomalyIndex': 'Target: coherence proxy (0-1, lower=more coherent)',
            'Asymmetry': '|A-2Z|/A — neutron-proton asymmetry',
            'logT12': 'log10(HalfLife_seconds + 1)',
            'Z_magic': '1 if Z is magic number (2,8,20,28,50,82,126)',
            'N_magic': '1 if N is magic number',
            'Double_magic': '1 if both Z and N are magic'
        },
        'acknowledgements': 'Nuclear data from AME2020 (IAEA). IAO is a synthetic target for ARKHE research.'
    }

    # Save dataset files
    df.to_csv(output_path / 'nuclear_coherence.csv', index=False)

    # Save feature-engineered version
    df_engineered.to_csv(output_path / 'nuclear_coherence_engineered.csv', index=False)

    # Save metadata
    with open(output_path / 'dataset_info.json', 'w') as f:
        json.dump(dataset_info, f, indent=2)

    # Create Kaggle dataset metadata
    kaggle_meta = {
        'title': dataset_info['title'],
        'id': f'arkhe-os/nuclear-coherence',
        'licenses': [{'name': dataset_info['license']}],
        'resources': [
            {
                'path': 'nuclear_coherence.csv',
                'description': 'Raw nuclear properties + IAO target'
            },
            {
                'path': 'nuclear_coherence_engineered.csv',
                'description': 'With engineered features for ML'
            }
        ]
    }
    with open(output_path / 'dataset-metadata.json', 'w') as f:
        json.dump(kaggle_meta, f, indent=2)

    # Create example notebook
    notebook = f'''# 🌲 ARKHE Tabula: Nuclear Coherence Exploration

## Setup
```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

df = pd.read_csv('nuclear_coherence_engineered.csv')
```

## Quick EDA
```python
# Distribution of IAO
df['OctonionicAnomalyIndex'].hist(bins=50)
plt.title('Octonionic Anomaly Index Distribution')
plt.xlabel('IAO'); plt.ylabel('Count')
plt.show()

# CAPTURE-like nuclides (IAO < 0.3)
capture = df[df['OctonionicAnomalyIndex'] < 0.3]
print(f"CAPTURE-like: {{len(capture)}}/{{len(df)}} = {{len(capture)/len(df)*100:.1f}}%")
```

## Train a Simple Model
```python
feature_cols = [c for c in df.columns if c not in ['Z','N','A','OctonionicAnomalyIndex']]
X = df[feature_cols]
y = df['OctonionicAnomalyIndex']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X_train, y_train)

print(f"R²: {{model.score(X_test, y_test):.4f}}")
```

## Explore Feature Importance
```python
import pandas as pd
imp = pd.DataFrame({{
    'feature': feature_cols,
    'importance': model.feature_importances_
}}).sort_values('importance', ascending=False)

imp.head(10).plot(x='feature', y='importance', kind='barh')
plt.tight_layout()
plt.show()
```

---
*Dataset from ARKHE OS v∞.357 — Tabula Oracle*
'''
    with open(output_path / 'notebook.ipynb', 'w') as f:
        # Would use nbformat to create proper Jupyter notebook
        f.write(notebook)

    print(f"📦 Kaggle dataset prepared: {output_path}")
    print(f"🔗 Next: Upload via Kaggle CLI or web interface")
    print(f"   kaggle datasets create -p {output_path}")

    return output_path

if __name__ == '__main__':
    prepare_kaggle_dataset()
