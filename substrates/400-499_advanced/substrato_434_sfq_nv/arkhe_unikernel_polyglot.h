/*
 * arkhe_unikernel_polyglot.h — ARKHE OS Uni‑Kernel Polyglot Module
 * Substrate: 216-KM (Kernel Module Loadable)
 * Linux 6.8+ Compatible
 * Canonical Seal: c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4
 */

#ifndef _ARKHE_UNIKERNEL_POLYGLOT_H
#define _ARKHE_UNIKERNEL_POLYGLOT_H

#include <linux/types.h>
#include <linux/ioctl.h>

/* === Constantes auxiliares de ring (Ring0 kernel vs Ring3 user) === */
#define ARKHE_RING0_KERNEL 0
#define ARKHE_RING3_USER   3

/* === Magic number para o driver === */
#define ARKHE_UNI_MAGIC         0xA6

/* === System calls via ioctl === */
#define ARKHE_IOCTL_PARSE_LANG      _IOWR(ARKHE_UNI_MAGIC, 0, struct arkhe_uni_request)
#define ARKHE_IOCTL_VALIDATE_LANG   _IOWR(ARKHE_UNI_MAGIC, 1, struct arkhe_uni_request)
#define ARKHE_IOCTL_EXTRACT_CONSTRUCT _IOWR(ARKHE_UNI_MAGIC, 2, struct arkhe_uni_request)
#define ARKHE_IOCTL_SECURITY_SCAN_LANG _IOWR(ARKHE_UNI_MAGIC, 3, struct arkhe_uni_request)
#define ARKHE_IOCTL_GENERATE_TOKENS_LANG _IOWR(ARKHE_UNI_MAGIC, 4, struct arkhe_uni_request)
#define ARKHE_IOCTL_PHI_C_CALC_LANG _IOWR(ARKHE_UNI_MAGIC, 5, struct arkhe_uni_request)
#define ARKHE_IOCTL_AST_EXPORT_LANG _IOWR(ARKHE_UNI_MAGIC, 6, struct arkhe_uni_request)
#define ARKHE_IOCTL_REGISTER_LANGUAGE _IOW(ARKHE_UNI_MAGIC, 7, struct arkhe_lang_registration)
#define ARKHE_IOCTL_UNI_KERNEL_STATS _IOR(ARKHE_UNI_MAGIC, 8, struct arkhe_uni_kernel_stats)
#define ARKHE_IOCTL_BUS_PUBLISH_UNI _IOW(ARKHE_UNI_MAGIC, 9, struct arkhe_bus_message)
#define ARKHE_IOCTL_BUS_CONSUME_UNI _IOWR(ARKHE_UNI_MAGIC, 10, struct arkhe_bus_message)
#define ARKHE_IOCTL_FEDERATED_RULES_UPDATE _IOW(ARKHE_UNI_MAGIC, 11, struct arkhe_federated_rule)

/* === Linguagens suportadas (enum canônico) === */
enum arkhe_language {
    ARKHE_LANG_UNKNOWN = 0,
    ARKHE_LANG_PYTHON = 1,
    ARKHE_LANG_JAVASCRIPT = 2,
    ARKHE_LANG_TYPESCRIPT = 3,
    ARKHE_LANG_C = 4,
    ARKHE_LANG_CPP = 5,
    ARKHE_LANG_JAVA = 6,
    ARKHE_LANG_RUST = 7,
    ARKHE_LANG_GO = 8,
    ARKHE_LANG_RUBY = 9,
    ARKHE_LANG_CSHARP = 10,
    ARKHE_LANG_PHP = 11,
    ARKHE_LANG_COBOL = 12,
    ARKHE_LANG_SQL = 13,
    ARKHE_LANG_PLSQL = 14,
    ARKHE_LANG_JCL = 15,
    ARKHE_LANG_ABAP = 16,
    ARKHE_LANG_SWIFT = 17,
    ARKHE_LANG_KOTLIN = 18,
    ARKHE_LANG_MAX = 19
};

/* === Motores de parsing suportados === */
enum arkhe_parse_engine {
    ARKHE_ENGINE_TREE_SITTER = 1,
    ARKHE_ENGINE_ANTLR = 2,
    ARKHE_ENGINE_REGEX = 3,
    ARKHE_ENGINE_CUSTOM = 4
};

/* === Tipos de construct extraídos === */
enum arkhe_construct_type {
    ARKHE_CONSTRUCT_UNKNOWN = 0,
    ARKHE_CONSTRUCT_FUNCTION = 1,
    ARKHE_CONSTRUCT_TRANSACTION = 2,   /* CICS/IMS/DB2 */
    ARKHE_CONSTRUCT_QUERY = 3,          /* SQL/NoSQL */
    ARKHE_CONSTRUCT_API_CALL = 4,
    ARKHE_CONSTRUCT_CRYPTO_OP = 5,
    ARKHE_CONSTRUCT_FILE_IO = 6,
    ARKHE_CONSTRUCT_NETWORK_OP = 7,
    ARKHE_CONSTRUCT_PRIVILEGE_OP = 8,
    ARKHE_CONSTRUCT_DYNAMIC_CODE = 9    /* eval/exec/compile */
};

/* === Violações de segurança (expandidas para poliglota) === */
#define ARKHE_VIOL_DYNAMIC_CODE         0x0001  /* eval/exec em qualquer linguagem */
#define ARKHE_VIOL_UNSAFE_DESERIAL      0x0002  /* pickle/marshal/unsafe YAML */
#define ARKHE_VIOL_SQL_INJECT           0x0004  /* SQL injection pattern */
#define ARKHE_VIOL_CMD_INJECT           0x0008  /* command injection */
#define ARKHE_VIOL_PATH_TRAVERSAL       0x0010  /* ../../etc/passwd patterns */
#define ARKHE_VIOL_CRYPTO_WEAK          0x0020  /* MD5/SHA1/RC4 usage */
#define ARKHE_VIOL_PRIV_ESCALATION      0x0040  /* setuid/sudo pattern */
#define ARKHE_VIOL_HARDcoded_SECRET     0x0080  /* senhas/chaves em código */
#define ARKHE_VIOL_CICS_AUDIT           0x0100  /* CICS sem auditoria */
#define ARKHE_VIOL_IMS_AUDIT            0x0200  /* IMS sem auditoria */
#define ARKHE_VIOL_DB2_UNQUALIFIED      0x0400  /* DB2 sem WHERE em UPDATE/DELETE */
#define ARKHE_VIOL_ALTER_COBOL          0x0800  /* ALTER verb em COBOL */
#define ARKHE_VIOL_GOTO_DEP             0x1000  /* GO TO DEPENDING ON */
#define ARKHE_VIOL_PERFORM_THRU         0x2000  /* PERFORM THRU sem validação */
#define ARKHE_VIOL_UNSAFE_CONCURRENCY   0x4000  /* race condition patterns */

/* === Constantes de buffer === */
#define ARKHE_MAX_SOURCE_FRAGMENT   8192    /* 8KB para parsing em kernel */
#define ARKHE_MAX_PROGRAM_NAME      64
#define ARKHE_MAX_FUNCTION_NAME     128
#define ARKHE_MAX_RESOURCE_NAME     128
#define ARKHE_MAX_CONSTRUCTS        256
#define ARKHE_MAX_VIOLATIONS        128
#define ARKHE_MAX_TOKENS            512
#define ARKHE_MAX_BUS_MSG           2048

/* === Estruturas de dados canônicas === */

struct arkhe_construct {
    __u8    construct_type;           /* enum arkhe_construct_type */
    char    name[ARKHE_MAX_FUNCTION_NAME];
    __u32   line_number;
    __u32   column;
    char    resource[ARKHE_MAX_RESOURCE_NAME];  /* arquivo, tabela, endpoint */
    __u8    has_parameters;
    __u32   parameter_count;
    float   phi_c_local;              /* coerência local do construct */
};

struct arkhe_security_violation_uni {
    __u16   violation_type;           /* bitmask de ARKHE_VIOL_* */
    __u8    severity;                 /* 0=critical, 1=high, 2=medium, 3=low */
    __u32   line_number;
    __u32   column;
    char    description[256];
    char    language_specific[64];    /* ex: "COBOL:ALTER", "Python:eval" */
    float   phi_c_impact;
    __u8    auto_fixable;             /* 1 se ação de healing disponível */
};

struct arkhe_token_uni {
    __u8    header[32];               /* SHA3-256 truncated */
    char    identity[96];             /* "lang_construct_prog_line" */
    __u8    language;                 /* enum arkhe_language */
    __u8    construct_type;
    char    program[ARKHE_MAX_PROGRAM_NAME];
    char    resource[ARKHE_MAX_RESOURCE_NAME];
    float   phi_c_at_parse;
    __u64   timestamp;
    __u8    pqc_signed;               /* 1 se assinado com PQC */
};

struct arkhe_uni_request {
    /* Input */
    __u32   caller_pid;
    __u8    caller_ring;              /* ARKHE_RING0_* */
    __u8    language;                 /* enum arkhe_language ou 0=auto-detect */
    __u8    engine_preference;        /* engine preferido ou 0=auto */
    __u32   source_len;
    char    source_fragment[ARKHE_MAX_SOURCE_FRAGMENT];

    /* Output */
    char    program_name[ARKHE_MAX_PROGRAM_NAME];
    __u8    detected_language;
    __u8    engine_used;
    float   phi_c_score;
    __u32   construct_count;
    __u32   violation_count;
    __u32   token_count;

    /* Arrays de resultados */
    struct arkhe_construct constructs[ARKHE_MAX_CONSTRUCTS];
    struct arkhe_security_violation_uni violations[ARKHE_MAX_VIOLATIONS];
    struct arkhe_token_uni tokens[ARKHE_MAX_TOKENS];

    /* Métricas de execução */
    __u64   execution_cycles;
    __u64   parse_time_ns;
    float   kernel_phi_c;
    __s32   status;                   /* 0=OK, -1=ERROR, -2=PERMISSION_DENIED */
};

struct arkhe_lang_registration {
    char    language_name[32];
    __u8    language;                 /* enum arkhe_language */
    __u8    engine_type;              /* tree-sitter, antlr, regex */
    char    grammar_path[256];        /* caminho para gramática no kernel */
    __u32   grammar_hash[8];          /* SHA3-256 da gramática */
    __u8    enabled;
};

struct arkhe_uni_kernel_stats {
    char    substrate_id[16];         /* "216-KM" */
    float   kernel_phi_c;
    __u64   uptime_seconds;
    __u32   total_parses;
    __u32   languages_registered;
    __u32   constructs_extracted;
    __u32   violations_detected;
    __u32   tokens_generated;
    __u32   federated_rules_count;
    __u64   total_parse_cycles;
    __u32   bus_messages_published;
    __u32   bus_messages_consumed;
};

struct arkhe_federated_rule {
    char    rule_id[32];
    char    language[32];
    __u16   violation_type;
    char    pattern_regex[256];
    __u8    severity;
    char    description[256];
    char    recommendation[256];
    float   confidence;
    __u64   source_org_hash[4];       /* hash da organização fonte (anonimizado) */
    __u64   timestamp;
    __u8    pqc_signature[64];        /* assinatura PQC do agregador */
};

struct arkhe_bus_message {
    char    channel_name[32];
    __u32   sender_pid;
    char    sender_substrate[16];
    char    payload[ARKHE_MAX_BUS_MSG];
    __u32   payload_len;
};

/* === Protótipos de funções exportadas === */
extern int arkhe_uni_parse(struct arkhe_uni_request *req);
extern int arkhe_uni_security_scan(struct arkhe_uni_request *req);
extern float arkhe_uni_phi_c_calc(const char *source, __u8 language);
extern int arkhe_uni_generate_tokens(struct arkhe_uni_request *req);
extern int arkhe_uni_register_language(struct arkhe_lang_registration *reg);
extern int arkhe_uni_bus_publish(const char *channel, struct arkhe_bus_message *msg);
extern int arkhe_uni_bus_consume(const char *channel, __u32 pid, struct arkhe_bus_message *msg);

#endif /* _ARKHE_UNIKERNEL_POLYGLOT_H */
