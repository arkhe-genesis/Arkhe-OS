
    # MELT-PROTOCOL (Protocolo de Fusão de Segurança)

    ## Gatilhos de Ativação:
    1. BER > 10^-2 persistentemente por 1000 ciclos.
    2. Instabilidade de Fase (Kalman Innovation) > 0.5 rad.
    3. Drift de Frequência > 10 ppm (Inhomogeneidade Magnética Residual excedida).

    ## Procedimento:
    1. **SHUTDOWN_PHASE**: Desativar drivers de fase v_phi imediatamente.
    2. **THERMAL_DUMP**: Ativar dissipadores Graphene-TPU em potência máxima.
    3. **ENTROPY_INJECTION**: Injetar ruído branco no canal qhttp para evitar entalpia de informação.
    4. **HARD_RESET**: Reinicializar o controlador v_phi_controller após 500ms de estabilização térmica.
