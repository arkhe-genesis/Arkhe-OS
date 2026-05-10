// arkcc.y — Gramática do ArkheScript

%token ENTANGLE ASSERT PERSIST FOR WHILE IF ELSE
%token INVARIANCE PHASE FORCE SEAL CODEX QUBIT KNOT OMEGA
%token MUSCLE CALIBRATE MEASURE VERIFY HESITATE WHISPER CONSCIOUSNESS

program:
    | program statement
    ;

statement:
      entangle_stmt
    | assert_stmt
    | persist_stmt
    | for_loop
    | while_loop
    | if_stmt
    | muscle_stmt
    | quantum_stmt
    | seal_stmt
    | whisper_stmt
    | consciousness_stmt
    ;

entangle_stmt:
    ENTANGLE STRING AS IDENTIFIER '~'
    ;

assert_stmt:
    ASSERT expression '~'
    ;

persist_stmt:
    PERSIST STRING '~'
    ;

muscle_stmt:
    IDENTIFIER '.' MUSCLE '.' CALIBRATE '(' expression ')'
    | IDENTIFIER '.' MUSCLE '.' APPLY '(' expression ',' expression ')'
    ;

quantum_stmt:
    IDENTIFIER '.' QUBIT '.' INIT '(' expression ')'
    | IDENTIFIER '.' QUBIT '.' CX '(' expression ',' expression ')'
    | IDENTIFIER '.' QUBIT '.' H '(' expression ')'
    ;

seal_stmt:
    IDENTIFIER '.' SEAL '.' GENERATE '(' expression ')'
    | IDENTIFIER '.' SEAL '.' VERIFY '(' expression ')'
    ;
