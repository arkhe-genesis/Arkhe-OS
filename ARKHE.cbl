      *> ******************************************************************
      *> *  ARKHE Ω‑TEMP v4.5.0 — COBOL Core
      *> *  Substratos 5021, 333, 5033, 5034, 5035
      *> *
      *> *  Compilar (GnuCOBOL):
      *> *      cobc -x -free ARKHE.cbl
      *> *  Executar:
      *> *      ./ARKHE
      *> *
      *> *  Autor: Catedral (portado para mainframe)
      *> ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ARKHE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.

      *> ---------------------------------------------------------------
      *> CONSTANTES QUÂNTICAS
      *> ---------------------------------------------------------------
       01  WS-CONSTANTS.
           05  PLANCK-HBAR       PIC 9(12)V9(12) VALUE 1.054571817E-34.
           05  QUANTUM-WINDOW    PIC 9(12)V9(12) VALUE 0.000000000001.
           05  MAX-WINDOW-SEC    PIC 9(12)V9(12) VALUE 157788000.
           05  PI                PIC 9(1)V9(15) VALUE 3.141592653589793.

      *> ---------------------------------------------------------------
      *> CRISTAL DE TEMPO (5021)
      *> ---------------------------------------------------------------
       01  WS-TIME-CRYSTAL.
           05  TC-OMEGA          PIC 9(12)V9(4) VALUE 2920000.0.
           05  TC-START-TIME     PIC 9(12)V9(6) VALUE 0.
           05  TC-PHASE          PIC 9(12)V9(15) VALUE 0.

      *> ---------------------------------------------------------------
      *> LEDGER DE AUDITORIA (333) — entrada fixa
      *> ---------------------------------------------------------------
       01  WS-LEDGER-ENTRIES.
           05  WS-LEDGER-COUNT   PIC 9(4) VALUE 0.
           05  WS-LEDGER-TABLE.
               10  WS-LEDGER-ENTRY OCCURS 10 TIMES
                                   INDEXED BY LX.
                   15  LE-TYPE    PIC X(30).
                   15  LE-PAYLOAD PIC X(200).
                   15  LE-TS      PIC 9(12)V9(6).
                   15  LE-HASH    PIC X(64).

      *> ---------------------------------------------------------------
      *> MENSAGEM TEMPORAL
      *> ---------------------------------------------------------------
       01  WS-TEMPORAL-MSG.
           05  TM-ID           PIC X(16).
           05  TM-CONTENT      PIC X(80).
           05  TM-SOURCE-TS    PIC 9(12)V9(6).
           05  TM-TARGET-TS    PIC 9(12)V9(6).
           05  TM-SENDER       PIC X(20).
           05  TM-RECEIVER     PIC X(20).

      *> ---------------------------------------------------------------
      *> RELATÓRIO DE CONSISTÊNCIA
      *> ---------------------------------------------------------------
       01  WS-CONSISTENCY-REPORT.
           05  CR-CONSISTENT   PIC X(4).
           05  CR-SCORE        PIC 9(1)V9(6).
           05  CR-PARADOX      PIC X(30).
           05  CR-QUANTUM      PIC X(4).

      *> ---------------------------------------------------------------
      *> CADEIA TEMPORAL (5033) — tabela fixa
      *> ---------------------------------------------------------------
       01  WS-CHAIN.
           05  WS-CHAIN-COUNT  PIC 9(4) VALUE 1.
           05  WS-BLOCKS.
               10  WS-BLOCK OCCURS 50 TIMES
                            INDEXED BY BX.
                   15  BLK-INDEX   PIC 9(4).
                   15  BLK-TS      PIC S9(12)V9(6).
                   15  BLK-PREV    PIC X(64).
                   15  BLK-DATA    PIC X(64).
                   15  BLK-DEPTH   PIC 9(4)V9(6).
                   15  BLK-HASH    PIC X(64).

      *> ---------------------------------------------------------------
      *> VARIÁVEIS AUXILIARES
      *> ---------------------------------------------------------------
       01  WS-CURRENT-TIME    PIC 9(12)V9(6).
       01  WS-DELTA           PIC S9(12)V9(6).
       01  WS-TEMP-SCORE      PIC 9(1)V9(6).
       01  WS-I               PIC 9(4).
       01  WS-J               PIC 9(4).
       01  WS-FUNC-RESULT     PIC 9(5).

      *> ---------------------------------------------------------------
      *> GERADOR DE HASH SIMPLES (CHECKSUM)
      *> ---------------------------------------------------------------
       01  WS-HASH-INPUT      PIC X(200).
       01  WS-HASH-OUTPUT     PIC X(64).
       01  WS-HASH-CHAR       PIC X(1).
       01  WS-HASH-SUM        PIC 9(4).

       PROCEDURE DIVISION.

       MAIN SECTION.
           DISPLAY '**************************************************'
           DISPLAY '*  ARKHE Ω‑TEMP v4.5.0 — COBOL Core             *'
           DISPLAY '*  A Catedral no Mainframe                     *'
           DISPLAY '**************************************************'

           PERFORM INIT-TIME-CRYSTAL
           PERFORM INIT-GENESIS-BLOCK

           DISPLAY ' '
           DISPLAY '--- Teste 1: Mensagem para o futuro (+120s) ---'
           MOVE 'MSG-FUTURO-001'  TO TM-ID
           MOVE 'Ola do passado'  TO TM-CONTENT
           ACCEPT WS-CURRENT-TIME FROM TIME
           MOVE WS-CURRENT-TIME   TO TM-SOURCE-TS
           COMPUTE TM-TARGET-TS = WS-CURRENT-TIME + 120
           MOVE 'ALFA-01'         TO TM-SENDER
           MOVE 'BETA-02'         TO TM-RECEIVER
           PERFORM EVALUATE-MESSAGE
           DISPLAY 'Score: ' CR-SCORE
           DISPLAY 'Consistente: ' CR-CONSISTENT
           DISPLAY 'Paradoxo: ' CR-PARADOX

           IF CR-CONSISTENT = 'SIM'
               PERFORM INSERT-INTO-CHAIN
               DISPLAY 'Bloco inserido na cadeia. Length: ' WS-CHAIN-COUNT
           END-IF

           DISPLAY ' '
           DISPLAY '--- Teste 2: Mensagem paradóxica (Δt < -1s) ---'
           MOVE 'MSG-PARADOX-001' TO TM-ID
           COMPUTE TM-TARGET-TS = WS-CURRENT-TIME - 2.0
           MOVE 'ALFA-01'         TO TM-SENDER
           MOVE 'BETA-02'         TO TM-RECEIVER
           PERFORM EVALUATE-MESSAGE
           DISPLAY 'Score: ' CR-SCORE
           DISPLAY 'Consistente: ' CR-CONSISTENT
           DISPLAY 'Paradoxo: ' CR-PARADOX

           DISPLAY ' '
           DISPLAY '--- Status da Cadeia Temporal ---'
           DISPLAY 'Blocos na cadeia: ' WS-CHAIN-COUNT
           PERFORM DISPLAY-CHAIN

           STOP RUN.

      *> =============================================================
      *> SUBROTINAS
      *> =============================================================

       INIT-TIME-CRYSTAL.
           ACCEPT WS-CURRENT-TIME FROM TIME
           MOVE WS-CURRENT-TIME TO TC-START-TIME
           DISPLAY 'Cristal de Tempo iniciado. ω = ' TC-OMEGA.

       INIT-GENESIS-BLOCK.
           COMPUTE WS-CURRENT-TIME = 0.0
           MOVE 1 TO WS-CHAIN-COUNT
           MOVE 0 TO BLK-INDEX(1)
           MOVE 0.0 TO BLK-TS(1)
           MOVE ALL '0' TO BLK-PREV(1)
           MOVE 'ARKHE_GENESIS' TO WS-HASH-INPUT
           PERFORM COMPUTE-HASH
           MOVE WS-HASH-OUTPUT TO BLK-DATA(1)
           MOVE 'GENESIS' TO WS-HASH-INPUT
           PERFORM COMPUTE-HASH
           MOVE WS-HASH-OUTPUT TO BLK-HASH(1)
           MOVE 0.0 TO BLK-DEPTH(1).

       EVALUATE-MESSAGE.
           MOVE 1.0 TO CR-SCORE
           MOVE 'SIM' TO CR-CONSISTENT
           MOVE SPACES TO CR-PARADOX
           MOVE 'NÃO' TO CR-QUANTUM

           COMPUTE WS-DELTA = TM-TARGET-TS - TM-SOURCE-TS

      *>    Check 1: Coerência temporal
           IF FUNCTION ABS(WS-DELTA) > MAX-WINDOW-SEC
               MOVE 0.3 TO CR-SCORE
               MOVE 'NÃO' TO CR-CONSISTENT
               MOVE 'FORA_DA_JANELA' TO CR-PARADOX
               EXIT PARAGRAPH
           END-IF

      *>    Check 2: Tempo negativo quântico?
           IF WS-DELTA < 0 AND FUNCTION ABS(WS-DELTA) <= QUANTUM-WINDOW
               MOVE 'SIM' TO CR-QUANTUM
               COMPUTE CR-SCORE = CR-SCORE + 0.05
               EXIT PARAGRAPH
           END-IF

      *>    Check 3: Penalidade para tempo negativo clássico
           IF WS-DELTA < 0 AND FUNCTION ABS(WS-DELTA) > QUANTUM-WINDOW
               COMPUTE WS-TEMP-SCORE = 1.0 -
                   (FUNCTION ABS(WS-DELTA) / MAX-WINDOW-SEC)
               IF WS-TEMP-SCORE > 0.3
                   MOVE 0.3 TO WS-TEMP-SCORE
               END-IF
               IF WS-TEMP-SCORE < CR-SCORE
                   MOVE WS-TEMP-SCORE TO CR-SCORE
               END-IF
               IF WS-TEMP-SCORE < 0.5
                   MOVE 'PARADOXO_GRANDPARENT' TO CR-PARADOX
                   MOVE 'NÃO' TO CR-CONSISTENT
               END-IF
           END-IF

      *>    Check 4: Entropia segura
           COMPUTE WS-TEMP-SCORE = 1.0 - (LENGTH OF TM-CONTENT * 8) /
               (1024 * 1024 * 8)
           IF WS-TEMP-SCORE < 0
               MOVE 0.0 TO WS-TEMP-SCORE
           END-IF
           IF WS-TEMP-SCORE < CR-SCORE
               MOVE WS-TEMP-SCORE TO CR-SCORE
           END-IF.

       INSERT-INTO-CHAIN.
           ADD 1 TO WS-CHAIN-COUNT
           MOVE WS-CHAIN-COUNT TO BLK-INDEX(WS-CHAIN-COUNT)
           MOVE TM-TARGET-TS TO BLK-TS(WS-CHAIN-COUNT)
           MOVE BLK-HASH(WS-CHAIN-COUNT - 1) TO BLK-PREV(WS-CHAIN-COUNT)
           MOVE TM-CONTENT TO WS-HASH-INPUT
           PERFORM COMPUTE-HASH
           MOVE WS-HASH-OUTPUT TO BLK-DATA(WS-CHAIN-COUNT)
      *>    Compute block hash (prev + data)
           STRING BLK-PREV(WS-CHAIN-COUNT) DELIMITED BY SIZE
                  BLK-DATA(WS-CHAIN-COUNT) DELIMITED BY SIZE
                  INTO WS-HASH-INPUT
           END-STRING
           PERFORM COMPUTE-HASH
           MOVE WS-HASH-OUTPUT TO BLK-HASH(WS-CHAIN-COUNT)
           COMPUTE BLK-DEPTH(WS-CHAIN-COUNT) =
               FUNCTION ABS(WS-DELTA) / (365.25 * 86400).

       DISPLAY-CHAIN.
           PERFORM VARYING WS-I FROM 1 BY 1
                   UNTIL WS-I > WS-CHAIN-COUNT
               DISPLAY 'Bloco #' BLK-INDEX(WS-I)
                       ' TS:' BLK-TS(WS-I)
                       ' Hash:' BLK-HASH(WS-I)(1:16)
           END-PERFORM.

       COMPUTE-HASH.
           MOVE 0 TO WS-HASH-SUM
           PERFORM VARYING WS-J FROM 1 BY 1
                   UNTIL WS-J > FUNCTION LENGTH(WS-HASH-INPUT)
               MOVE WS-HASH-INPUT(WS-J:1) TO WS-HASH-CHAR
               COMPUTE WS-FUNC-RESULT = FUNCTION ORD(WS-HASH-CHAR)
               ADD WS-FUNC-RESULT TO WS-HASH-SUM
           END-PERFORM
           STRING WS-HASH-SUM DELIMITED BY SIZE INTO WS-HASH-OUTPUT.

       END PROGRAM ARKHE.
