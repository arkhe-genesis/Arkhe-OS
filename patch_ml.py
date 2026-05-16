with open("ml/zero_day_production_trainer.py", "r") as f:
    content = f.read()

target_block1 = """        # Mock: em produção, consultar banco de dados de telemetria
        n_samples = days_back * 1000  # ~1000 amostras/dia"""

new_block1 = """        # Mock: em produção, consultar banco de dados de telemetria
        n_samples = days_back * 1000  # ~1000 amostras/dia"""

target_block2 = """            # Em produção: usar labels de incidentes confirmados
            is_zero_day = np.random.random() < 0.02  # 2% de zero-days no dataset"""

new_block2 = """            # Em produção: usar labels de incidentes confirmados
            is_zero_day = np.random.random() < 0.02  # 2% de zero-days no dataset"""

target_block3 = """        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        ) """

new_block3 = """        # Split train/test
        if len(np.unique(y)) > 1:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            ) """

target_block4 = """        # Avaliar no conjunto de teste
        logger.info("   📊 Avaliando modelo...")
        y_pred_if = self._isolation_forest.predict(X_test)
        y_pred_rf = self._classifier.predict(X_test) """

new_block4 = """        # Avaliar no conjunto de teste
        logger.info("   📊 Avaliando modelo...")
        y_pred_if = self._isolation_forest.predict(X_test)
        if len(np.unique(y_train)) > 1:
            y_pred_rf = self._classifier.predict(X_test)
        else:
            y_pred_rf = np.zeros(len(X_test))"""


target_block5 = """        # Ensemble score (ponderado)
        # IF: score mais baixo = mais anômalo → inverter e normalizar
        if_normalized = 1 - (if_score + 1) / 2  # Mapear [-1, 0] → [0, 1]
        ensemble_score = if_normalized * 0.4 + rf_score * 0.6 """

new_block5 = """        # Ensemble score (ponderado)
        # IF: score mais baixo = mais anômalo → inverter e normalizar
        if_normalized = 1 - (if_score + 1) / 2  # Mapear [-1, 0] → [0, 1]
        ensemble_score = if_normalized * 0.4 + (rf_score if isinstance(rf_score, (int, float)) else rf_score[0]) * 0.6 """

if target_block3 in content:
    content = content.replace(target_block3, new_block3)
if target_block4 in content:
    content = content.replace(target_block4, new_block4)
if target_block5 in content:
    content = content.replace(target_block5, new_block5)

with open("ml/zero_day_production_trainer.py", "w") as f:
    f.write(content)
print("Patched successfully")
