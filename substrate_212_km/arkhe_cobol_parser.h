/*
 * arkhe_cobol_parser.h — ARKHE OS Kernel COBOL Parser Module
 * Substrate: 212-KM (Kernel Module Loadable)
 * Linux 6.8 Compatible
 * Canonical Seal: bfbc03900123006c35442cf12f2d0189b0496856d8eb3e23fbbbbe4e46cbf31e
 */

#ifndef _ARKHE_COBOL_PARSER_H
#define _ARKHE_COBOL_PARSER_H

#include <linux/types.h>
#include <linux/ioctl.h>

/* === Magic number para o driver === */
#define ARKHE_COBOL_MAGIC       0xA2

/* === System calls via ioctl === */
#define ARKHE_IOCTL_PARSE           _IOWR(ARKHE_COBOL_MAGIC, 0, struct arkhe_cobol_request)
#define ARKHE_IOCTL_VALIDATE        _IOWR(ARKHE_COBOL_MAGIC, 1, struct arkhe_cobol_request)
#define ARKHE_IOCTL_EXTRACT_CICS    _IOWR(ARKHE_COBOL_MAGIC, 2, struct arkhe_cobol_request)
#define ARKHE_IOCTL_EXTRACT_IMS     _IOWR(ARKHE_COBOL_MAGIC, 3, struct arkhe_cobol_request)
#define ARKHE_IOCTL_EXTRACT_DB2     _IOWR(ARKHE_COBOL_MAGIC, 4, struct arkhe_cobol_request)
#define ARKHE_IOCTL_SECURITY_SCAN   _IOWR(ARKHE_COBOL_MAGIC, 5, struct arkhe_cobol_request)
#define ARKHE_IOCTL_TOKEN_GENERATE  _IOWR(ARKHE_COBOL_MAGIC, 6, struct arkhe_cobol_request)
#define ARKHE_IOCTL_PHI_C_CALC      _IOWR(ARKHE_COBOL_MAGIC, 7, struct arkhe_cobol_request)
#define ARKHE_IOCTL_AST_EXPORT      _IOWR(ARKHE_COBOL_MAGIC, 8, struct arkhe_cobol_request)
#define ARKHE_IOCTL_KERNEL_STATS    _IOR(ARKHE_COBOL_MAGIC, 9, struct arkhe_kernel_stats)
#define ARKHE_IOCTL_BUS_PUBLISH     _IOW(ARKHE_COBOL_MAGIC, 10, struct arkhe_bus_message)
#define ARKHE_IOCTL_BUS_CONSUME     _IOWR(ARKHE_COBOL_MAGIC, 11, struct arkhe_bus_message)

/* === Privilege rings === */
#define ARKHE_RING0_KERNEL      0
#define ARKHE_RING1_DRIVER      1
#define ARKHE_RING2_SERVICE     2
#define ARKHE_RING3_USER        3

/* === Security violation types === */
#define ARKHE_VIOL_ALTER            0x01
#define ARKHE_VIOL_GOTO_DEP         0x02
#define ARKHE_VIOL_PERFORM_THRU     0x04
#define ARKHE_VIOL_SQL_INJECT       0x08
#define ARKHE_VIOL_CICS_AUDIT       0x10
#define ARKHE_VIOL_IMS_AUDIT        0x20
#define ARKHE_VIOL_UNQUAL_ACCESS    0x40
#define ARKHE_VIOL_DEAD_CODE        0x80

/* === CICS command types === */
#define ARKHE_CICS_READ         0x01
#define ARKHE_CICS_WRITE        0x02
#define ARKHE_CICS_REWRITE      0x03
#define ARKHE_CICS_DELETE       0x04
#define ARKHE_CICS_START        0x05
#define ARKHE_CICS_RETURN       0x06
#define ARKHE_CICS_WRITEQ_TD    0x07
#define ARKHE_CICS_READQ_TD     0x08

/* === IMS function types === */
#define ARKHE_IMS_GU            0x01
#define ARKHE_IMS_GN            0x02
#define ARKHE_IMS_GNP           0x03
#define ARKHE_IMS_GHU           0x04
#define ARKHE_IMS_GHN           0x05
#define ARKHE_IMS_ISRT          0x06
#define ARKHE_IMS_DLET          0x07
#define ARKHE_IMS_REPL          0x08

/* === DB2 statement types === */
#define ARKHE_DB2_SELECT        0x01
#define ARKHE_DB2_INSERT        0x02
#define ARKHE_DB2_UPDATE        0x03
#define ARKHE_DB2_DELETE        0x04
#define ARKHE_DB2_OPEN          0x05
#define ARKHE_DB2_CLOSE         0x06
#define ARKHE_DB2_FETCH         0x07

/* === Estruturas de dados === */

#define ARKHE_MAX_PROGRAM_ID    32
#define ARKHE_MAX_RESOURCE      64
#define ARKHE_MAX_TABLE         64
#define ARKHE_MAX_COPYBOOK      32
#define ARKHE_MAX_FRAGMENT      4096
#define ARKHE_MAX_TOKENS        256
#define ARKHE_MAX_VIOLATIONS    64
#define ARKHE_MAX_CICS_TXN      128
#define ARKHE_MAX_IMS_CALL      128
#define ARKHE_MAX_DB2_STMT      128
#define ARKHE_MAX_BUS_MSG       1024

struct arkhe_cics_transaction {
    __u8    command;
    char    resource[ARKHE_MAX_RESOURCE];
    __u32   line_number;
    __u8    has_transid;
    char    transid[8];
};

struct arkhe_ims_call {
    __u8    function;
    char    pcb_name[16];
    char    segment_name[32];
    __u32   line_number;
};

struct arkhe_db2_statement {
    __u8    statement_type;
    char    table[ARKHE_MAX_TABLE];
    __u32   line_number;
    __u8    has_where_clause;
};

struct arkhe_security_violation {
    __u8    violation_type;
    __u8    severity;       /* 0=critical, 1=high, 2=medium, 3=low */
    __u32   line_number;
    __u32   column;
    char    description[128];
    float   phi_c_impact;
};

struct arkhe_token {
    __u8    header[32];     /* SHA3-256 truncated */
    char    identity[64];
    __u8    semantics;      /* 1=CICS, 2=IMS */
    char    program[ARKHE_MAX_PROGRAM_ID];
    __u8    command_or_function;
    char    resource_or_pcb[ARKHE_MAX_RESOURCE];
    float   phi_c_at_parse;
    __u64   timestamp;
};

struct arkhe_cobol_request {
    __u32   caller_pid;
    __u8    caller_ring;
    __u32   source_len;
    char    source_fragment[ARKHE_MAX_FRAGMENT];

    /* Output */
    char    program_id[ARKHE_MAX_PROGRAM_ID];
    float   phi_c_score;
    __u32   cics_count;
    __u32   ims_count;
    __u32   db2_count;
    __u32   violation_count;
    __u32   token_count;

    struct arkhe_cics_transaction cics_txns[ARKHE_MAX_CICS_TXN];
    struct arkhe_ims_call ims_calls[ARKHE_MAX_IMS_CALL];
    struct arkhe_db2_statement db2_stmts[ARKHE_MAX_DB2_STMT];
    struct arkhe_security_violation violations[ARKHE_MAX_VIOLATIONS];
    struct arkhe_token tokens[ARKHE_MAX_TOKENS];

    __u64   execution_cycles;
    float   kernel_phi_c;
    __s32   status;         /* 0=OK, -1=ERROR, -2=PERMISSION_DENIED */
};

struct arkhe_kernel_stats {
    char    substrate_id[16];
    float   kernel_phi_c;
    __u64   uptime_seconds;
    __u32   total_pages;
    __u32   free_pages;
    __u32   allocated_pages;
    float   fragmentation_ratio;
    __u32   interrupts_raised;
    __u32   interrupts_pending;
    __u32   interrupts_handled;
    __u32   handlers_registered;
    __u64   total_syscall_cycles;
    __u32   total_syscalls;
    __u32   bus_channels;
    __u32   bus_subscribers;
    __u64   bus_messages;
};

struct arkhe_bus_message {
    char    channel_name[32];
    __u32   msg_id;
    __u32   sender_pid;
    char    sender_substrate[16];
    __u64   timestamp;
    float   phi_c_at_send;
    __u32   payload_len;
    char    payload[ARKHE_MAX_BUS_MSG];
    __u8    consumed_count;
    __u32   consumed_by[8];
};

/* === Protótipos de funções === */
extern int arkhe_cobol_parse(struct arkhe_cobol_request *req);
extern int arkhe_cobol_security_scan(struct arkhe_cobol_request *req);
extern float arkhe_kernel_phi_c_calc(void);
extern int arkhe_bus_publish(const char *channel, struct arkhe_bus_message *msg);
extern int arkhe_bus_consume(const char *channel, __u32 pid, struct arkhe_bus_message *msg);

#endif /* _ARKHE_COBOL_PARSER_H */