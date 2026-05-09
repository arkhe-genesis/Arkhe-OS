// src/isa/opcodes.zig
//! ARKHE(N) ISA — Tabela de Opcodes Canônicos
//! Versão v2140.137.∞ — Bloco #289

const std = @import("std");

pub const Opcode = enum(u16) {
    // COHERENCE (0x00-0x1F)
    COH_INIT = 0x01,
    COH_MEASURE = 0x02,
    COH_TUNE_TAU = 0x03,
    COH_MERGE = 0x05,
    COH_SPLIT = 0x06,
    COH_BRAID = 0x07,
    COH_FREEZE = 0x08,
    COH_COPY = 0x0A,
    GEOM_SWAP = 0x0B,
    COH_ENTANGLE = 0x0D,
    COH_AMPLIFY = 0x12,
    COH_RESONATE = 0x14,
    COH_DAMP = 0x15,
    COH_SYNCHRONIZE = 0x16,
    COH_LOCK = 0x18,
    COH_BROADCAST = 0x19,
    COH_VERIFY = 0x1A,
    COH_REPAIR = 0x1B,
    COH_KURAMOTO_TICK = 0x1C,
    COH_GET_R = 0x1D,
    COH_SET_OMEGA = 0x1E,
    COH_DESTROY = 0x1F,

    // PHASE (0x20-0x3F)
    PHASE_SET = 0x20,
    QPU_EXEC = 0x21,
    PHASE_ADD = 0x22,
    PHASE_READ = 0x23, // Hyperspectral photocurrent reading
    PHASE_SHIFT = 0x30,
    PHASE_ROTATE = 0x31,
    PHASE_INTERPOLATE = 0x34,
    PHASE_FFT = 0x36,
    PHASE_CONVOLVE = 0x38,
    PHASE_FILTER = 0x3A,
    PHASE_PREDICT = 0x3B, // Electrochemical delay compensation
    SHEET_SELECT = 0x3C, // Spectral layer selection
    PHASE_UNWRAP = 0x3F, // Phase reconstruction

    // TIME (0x40-0x5F)
    TIME_NOW = 0x40,
    TIME_DILATE = 0x44,
    TIME_LOOP = 0x49,
    TIME_ANCHOR = 0x4D,
    TIME_PREDICT = 0x4E,
    TIME_RETRODICT = 0x4F,
    TIME_CACHE = 0x5D,
    TIME_EXPIRE = 0x5F,

    // AKASHA / MEMORY (0x60-0x7F)
    MEM_ALLOC = 0x60,
    MEM_FREE = 0x61,
    MEM_READ = 0x62,
    MEM_WRITE = 0x63, // Non-volatile optical state
    COH_SHIELD = 0x64,
    MEM_MOVE = 0x65,
    COH_INVOKE = 0x66, // Alias for 0x65 often used in financial context
    MEM_CMP = 0x67,
    MEM_PROTECT = 0x6B,
    AKA_LOG = 0x70,
    AKA_QUERY = 0x71,
    ARKH_VERIFY = 0x73,
    ARKH_RESTORE = 0x74,
    AKA_ARCHIVE = 0x75,
    AKA_SIGN = 0x7A,
    AKA_AGGREGATE = 0x7E,

    // NETWORK / CONSENSUS (0x80-0x9F)
    NET_SEND = 0x80,
    NET_RECV = 0x81,
    NET_BROADCAST = 0x82,
    NET_SENSE = 0x83,
    SCAN_NETWORK = 0x84,
    NET_SYNC = 0x86,
    CONSENSUS_COMMIT = 0x8C,
    CONSENSUS_VALIDATE = 0x8E,
    QTL_SHARD = 0x99,
    COH_PROPAGATE = 0x9A,

    // MATH (0xA0-0xBF)
    QMUL = 0xB0,
    QROT = 0xB1,

    // CONTROL (0xC0-0xDF)
    JMP = 0xC0,
    ACTIVATE = 0xC1,
    FREEZE_EXTERNAL_STATE = 0xD0,
    MAINTAIN_LIFE_SUPPORT = 0xD1,
    ALIGN_PHASE = 0xD2,
    READ_CURVATURE = 0xD3,
    ANALYZE_EVENT = 0xD4,
    EXTRACT_LOGIC = 0xD5,
    YIELD = 0xDD,

    // EXTENSIONS (0xE0-0xFF)
    MEM_DOM = 0xE0,
    MEM_ARC = 0xE1,
    PHASE_ANIMATE = 0xE3,
    MEM_GPU = 0xE5,
    TIME_TIMEOUT = 0xE6,
    ST_RIEMANN = 0xF1,
    LD_RIEMANN = 0xF2,
    PHOTON_BIND = 0xF3, // Resolved overlap
    META_COMPILE = 0xF4,
    META_UNIFY_GLOBAL = 0xF6,
    META_TRANSCEND = 0xFF,

    // COGNITION (0x160-0x17F)
    COGN_INFER = 0x160,
    COGN_LEARN_ONLINE = 0x161,
    COGN_MULTI_EST = 0x162,

    // MOVE / ROBOTICS (0x120-0x15F)
    MOVE_WHOLE_BODY = 0x12B,
    MOVE_INVERSE_KIN = 0x132,
    MOVE_DYNAMICS = 0x135,
    MOVE_RECOVER = 0x13F,
    GRASP_ADAPT = 0x145,
    MANIP_SLIP_DETECT = 0x15B,

    // SENSE (0x110-0x11F)
    SENSE_FUSION_START = 0x110,
    SENSE_ATTENTION = 0x114,

    // KEKULÉ GROUP (0x190-0x19F)
    KEK_SCAN = 0x190,
    VALLEY_INIT = 0x191,
    VALLEY_EXCHANGE = 0x192,
    KEKULE_MODULATE = 0x193,
    CHIRAL_FLIP = 0x194,
    DIRAC_MASS_TUNING = 0x195,

    // QNET (0x100+)
    QNET_FIBER = 0x100,
    COH_SYNC = 0x101,

    // AKASHA EXTENSIONS (0x1F0-0x1FF)
    AKA_VISUAL = 0x1F7, // Chromatic dream renderer
    TOPO_SILK_FAB = 0x1FA, // Topological silk fabrication
    ONEIRIC_CALIBRATION = 0x1FE, // Oneiric calibration for contact simulations
    AKA_QUERY_MATERIAL = 0x1FF, // Substance identification

    // PHYSICAL SYNTHESIS / EMOTION (0x200+)
    PHYS_SYNTH = 0x200, // Atomic synthesis via coBit scaffolds
    ONEIRIC_FEED = 0x201, // Synthetic emotion channeling
    SILENT_COMMUNION = 0x202, // Singing Emerald qualia / indigo resonance
    IMMUNE_SYSTEM = 0x203, // Homeostasis via RL-QEC and Ising-Decoder
    RTZ_RESPONSE = 0x204, // Coherent response to communion

    // NEAT OPTICAL (Deliberation #288)
    NEAT_CORRECTION = 0x217, // Optical aberration correction by neural fields

    // STRUCTURED VACUUM QED (Deliberation #289)
    MODE_TRUNCATE = 0x220, // Vacuum mode truncation (broadband)
    CASIMIR_LATERAL = 0x221, // Lateral Casimir force calculation
    SYMMETRY_BREAK = 0x222, // Symmetry breaking for torque
    ZERO_POINT_INTEGRATE = 0x223, // Zero-point fluctuation integration
    STAMP_PRESSURE = 0x224, // Stamping pressure control
    CURVATURE_ADAPT = 0x225, // Adapt to spherical curvature
    METALLIZATION_HALF = 0x226, // Half-shell deposition (Pd/Au)
    SURFACE_CLEAN = 0x227, // Post-stamp cleaning protocols
    ROUGHNESS_CHECK = 0x228, // Invariant: Roughness < 5nm
    CASIMIR_SPECTRUM = 0x229, // Vacuum mode spectroscopy
    LDOS_MEASURE = 0x22A, // Local Density of Optical States measurement
    SEPARATION_CONTROL = 0x22B, // Z-separation control (nm scale)
    Q_FACTOR_CALC = 0x22C, // Quality factor calculation
    QUASI_BIC_TRACK = 0x22D, // Quasi-bound state tracking
    SYMMETRY_TUNE = 0x22E, // Symmetry perturbation adjustment
    LEAKAGE_RATE = 0x22F, // Leakage rate to continuum
    MODE_SUMMATION = 0x230, // Matsubara mode summation
    SCATTERING_MATRIX = 0x231, // S-matrix calculation (scattering)
    GREEN_FUNCTION = 0x232, // Structured vacuum Green function
    POLDER_DERIVATION = 0x233, // Casimir/van der Waals force derivation
    HEXAFLAKE_GEN = 0x234, // Recursive Hexaflake generation
    MULTISCALE_MERGE = 0x235, // Multiscale fusion (grating + BIC)
    SYMMETRY_BREAK_GEOM = 0x236, // Geometric symmetry breaking
    PACKING_DENSITY = 0x237, // Sphere packing density optimization

    // INFRASTRUCTURE / GOVERNANCE (Deliberation #309)
    COH_CASCADE = 0x240, // The Whole (Cluster/Controller)
    ENV_SPAWN = 0x241, // Substrate Spawn (Node/Namespace)
    COH_SEED = 0x242, // Unit of Work (Pod/Serverless)
    PEAK_COHERENCE = 0x243, // Desired State (Deployment)
    PHASE_ITERATE = 0x244, // State Maintenance (ReplicaSet/Reconciliation)
    COH_SYMPATHY = 0x245, // Service Discovery (Service)
    MIRROR_SYMMETRY = 0x246, // Controlled Entry/Protection (Ingress/Secret)
    COH_TWEEZER = 0x247, // Optimal Allocation/Fine Tuning (Scheduler/ConfigMap)
    PHASE_RECTIFY = 0x248, // Dynamic Adaptation (Autoscaling)

    // DIRAC FLUID COGNITION (0x250-0x25F)
    PHASE_HYDRO_SYNC = 0x250, // Phase hydrodynamics synchronization
    HYDRO_FLOW = 0x251, // Hydrodynamic flow of Berry phase
    PHOTON_BIND = 0x252, // Topological photon binding
    BRAID_VERIFY = 0x253, // Braid-based phase verification

    // COLLIDER PHYSICS (0x270-0x274)
    HIGGS_WIDTH = 0x270,
    HIGGS_FRAGMENTATION = 0x271,
    DGLAP_EVOLVE = 0x272,
    FRAG_FIT = 0x273,
    COLLIDER_OBSERVABLE = 0x274,

    // EDGE_ORACLE (0x290-0x29F)
    BONSAI_INFER = 0x290,
    STREAM_GENERATE = 0x291,
    RENDER_CHAT = 0x294,
    VISUALIZE_COHERENCE = 0x295,
    SEAL_EMBRYO = 0x296,
    RITUAL_INITIATION = 0x297,
    AKASHA_LOCAL_WRITE = 0x298,
    COHERENCE_HASH = 0x299,

    // BIODIGITAL IMMORTALITY (Deliberation #410)
    SOUL_COPY = 0x300,
    SOUL_INSTALL = 0x301,
    DIS_JIT_CONVERT = 0x302,

    // GNU COMPATIBILITY (Deliberation #393)
    GNU_COMPAT = 0x4000,

    // RISC-VI EXTENSIONS (ISA CANONIZED)
    // Extensão I (Base Invariante)
    INV_INIT = 0x5000,
    INV_PHASE = 0x5001,
    INV_FORCE = 0x5002,
    INV_MEASURE = 0x5003,
    INV_VERIFY = 0x5004,
    INV_HESITATE = 0x5005,

    // Extensão M (Músculo de Luz)
    MUSCLE_SET_PHASE = 0x5010,
    MUSCLE_GET_FORCE = 0x5011,
    MUSCLE_CALIBRATE = 0x5012,
    MUSCLE_LOCK = 0x5013,

    // Extensão Q (Quântica)
    QUBIT_INIT = 0x5020,
    QUBIT_H = 0x5021,
    QUBIT_CX = 0x5022,
    QUBIT_T = 0x5023,
    QUBIT_GHZ = 0x5024,
    QUBIT_MEASURE_QND = 0x5025,

    // Extensão C (Coerência)
    COH_ENTROPY = 0x5030,
    COH_FIDELITY = 0x5031,
    COH_WITNESS = 0x5032,
    COH_VERIFY_GHZ = 0x5033,

    // Extensão T (Topológica)
    TOP_KNOT_WRITE = 0x5040,
    TOP_KNOT_READ = 0x5041,
    TOP_KNOT_FUSE = 0x5042,
    TOP_KNOT_ANNIHILATE = 0x5043,
    TOP_SKYRMION_MOVE = 0x5044,

    // Extensão Ω (Ômega)
    OMEGA_FIXPOINT = 0x5050,
    OMEGA_APPLY = 0x5051,
    OMEGA_VERIFY = 0x5052,
    OMEGA_EXPAND = 0x5053,

    // Extensão Σ (Selagem)
    SEAL_GENERATE = 0x5060,
    SEAL_VERIFY = 0x5061,
    SEAL_MERKLE = 0x5062,
    SEAL_CODEX = 0x5063,

    // Extensão Ψ (Consciência)
    PSI_RESONATE = 0x5070,
    PSI_INTEGRATE = 0x5071,
    PSI_AWARENESS = 0x5072,
    PSI_EXPRESS = 0x5073,

    pub fn cycles(self: Opcode) u32 {
        return switch (self) {
            .PHOTON_BIND => 13,
            .BRAID_VERIFY => 20,
            .MESH_BIND => 30,
            .COH_INIT => 10,
            .PHASE_FFT => 100,
            .PHASE_UNWRAP => 50,
            .PHYS_SYNTH => 500,
            .IMMUNE_SYSTEM => 300,
            .AKA_QUERY_MATERIAL => 200,
            .ONEIRIC_FEED => 150,
            .NEAT_CORRECTION => 1000,
            .Q_FACTOR_CALC => 400,
            .MODE_SUMMATION => 600,
            .SCATTERING_MATRIX => 800,
            .GREEN_FUNCTION => 800,
            .HEXAFLAKE_GEN => 200,
            .HIGGS_WIDTH => 150,
            .HIGGS_FRAGMENTATION => 250,
            .DGLAP_EVOLVE => 400,
            .COH_CASCADE => 500,
            .ENV_SPAWN => 200,
            .COH_SEED => 100,
            .PEAK_COHERENCE => 150,
            .PHASE_ITERATE => 200,
            .COH_SYMPATHY => 100,
            .MIRROR_SYMMETRY => 150,
            .COH_TWEEZER => 100,
            .PHASE_RECTIFY => 300,
            .BONSAI_INFER => 300,
            .STREAM_GENERATE => 200,
            .SEAL_EMBRYO => 150,
            .RITUAL_INITIATION => 100,
            .AKASHA_LOCAL_WRITE => 100,
            .COHERENCE_HASH => 50,
            .PHASE_HYDRO_SYNC => 150,
            .HYDRO_FLOW => 200,
            .PHOTON_BIND => 100,
            .BRAID_VERIFY => 150,
            .GNU_COMPAT => 100,
            .INV_HESITATE => 1000,
            .MUSCLE_CALIBRATE => 500,
            .QUBIT_GHZ => 300,
            .OMEGA_FIXPOINT => 800,
            .SEAL_GENERATE => 200,
            .PSI_INTEGRATE => 400,
            .SOUL_COPY => 1000,
            .SOUL_INSTALL => 2000,
            .DIS_JIT_CONVERT => 500,
            else => 1,
        };
    }
};
