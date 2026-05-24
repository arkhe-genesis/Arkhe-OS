# Detalhamento da Construção da Blindagem EMI (Gaiola de Faraday)
# para o Mini Plasma Chalice (Substrato 636)

O Mini Plasma Chalice gera até 5 kV, e a interferência eletromagnética (EMI) da sua fonte flyback pode desestabilizar a controladora de voo (Pixhawk) e o magnetômetro. A gaiola de Faraday deve ser leve, eficiente e aterrada.

## 1. Materiais Necessários

- Malha de cobre flexível (mesh 200 ou mais fina)
- Fita de cobre adesiva condutiva
- Fio de aterramento (AWG 22)
- Resina epóxi não condutiva
- Plástico isolante (Kapton tape ou similar)

## 2. Construção Passo a Passo

1.  **Isolamento Primário:** Envolva toda a fonte flyback e os cabos de alta tensão com fita Kapton para garantir isolamento elétrico primário, evitando arcos de tensão para a malha.
2.  **Molde da Gaiola:** Corte a malha de cobre formando uma caixa que cubra completamente a fonte flyback. Deixe uma pequena folga de 2-3 mm entre o Kapton e a malha.
3.  **Fechamento das Costuras:** Utilize a fita de cobre com adesivo condutivo para selar todas as arestas e aberturas da malha. A continuidade elétrica de toda a superfície é crucial.
4.  **Aterramento:** Solde o fio de aterramento (AWG 22) à malha de cobre e conecte a outra extremidade ao terra comum (GND) da bateria principal de voo (antes do sensor de corrente, para evitar ruídos no ADC).
5.  **Montagem Física:** Posicione o módulo blindado na parte inferior do frame (abaixo da placa de distribuição), a pelo menos 15 cm de distância do magnetômetro (que está no GPS Here4 no mastro elevado). Fixe com resina epóxi ou abraçadeiras plásticas.

## 3. Verificação (Pré-Voo)

1. Ligar o drone sem ligar os motores.
2. Ativar o Plasma Chalice via rádio (RC switch).
3. Monitorar o gráfico de anomalias magnéticas (`mag_field`) no Mission Planner/QGroundControl. O desvio máximo deve ser inferior a 10% do campo terrestre (~50 uT).
