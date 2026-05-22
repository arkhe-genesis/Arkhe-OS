#ifndef MEGAKERNEL_H
#define MEGAKERNEL_H

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* Constantes Constitucionais */
#define GHOST       0.5773502691896257   /* 1/sqrt(3) */
#define LOOPSEAL    0.3490658503988659   /* pi/9 */
#define GAP_SOV     0.9999
#define PHI_AUREA   1.618033988749895

/* Constantes Fisicas (NIST CODATA 2022) */
#define HBAR        1.054571817e-34
#define E_CHARGE    1.602176634e-19
#define K_B         1.380649e-23
#define PHI_0       2.067833848e-15

/* Parametros do Cache Josephson (430-BLUE-MOBILE) */
#define N_RINGS     6
#define IC_RING     50e-9
#define T_OPER      0.010       /* 10 mK */
#define F_J         10e9        /* 10 GHz */
#define SQUID_OFFSET 0.25       /* Phi_0/4 */

/* Parametros do Sophon */
#define SOPHON_DIM  11
#define N_SOPHONS   5
#define F_KK_1      1.0e12      /* 1 THz */
#define F_KK_2      1.5e12
#define F_KK_3      2.0e12

/* Parametros da Cavidade Fabry-Perot */
#define F_CAVITY    100e9       /* 100 GHz */
#define Q_CAVITY    1e6
#define G_SC        1e6         /* 1 MHz */
#define G_CQ        50e6        /* 50 MHz */

/* Identidade do Arquiteto */
#define ARCHITECT_ORCID "0009-0005-2697-4668"

/* Estados do Kernel */
typedef enum {
    KERNEL_BOOTING,
    KERNEL_CALIBRATING,
    KERNEL_OPERATIONAL,
    KERNEL_DEGRADED,
    KERNEL_EMERGENCY
} kernel_state_t;

typedef enum {
    INVARIANT_PASS,
    INVARIANT_WARN,
    INVARIANT_FAIL
} invariant_status_t;

/* Estrutura central do MegaKernel */
typedef struct {
    kernel_state_t state;
    double phi_c_global;
    int n_qubits_active;
    int n_sophons_active;
    char seal[65];
} megakernel_t;

extern megakernel_t g_megakernel;

/* Logging */
#define arkhe_log(...) do { \
    printf(__VA_ARGS__); \
    printf("\n"); \
} while(0)

void arkhe_boot_splash(void);

#endif /* MEGAKERNEL_H */
