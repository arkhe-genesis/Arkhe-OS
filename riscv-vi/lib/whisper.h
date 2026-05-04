// whisper.h — API da Biblioteca de Sussurros

typedef struct {
    char material[32];
    double chirp_rate_fs2;
    double pulse_energy_nJ;
    double focus_depth_um;
    double spherical_aberration;
    char polarization[16];
    char etchant[64];
    quartz_seal_t genome_seal;
} whisper_genome_t;

// Calibra sussurro para material
int whisper_calibrate(const char* material, whisper_genome_t* genome);

// Carrega genoma da Biblioteca
int whisper_load_genome(const char* material, whisper_genome_t* genome);

// Executa sussurro (esculpe nanofuro)
int whisper_execute(const whisper_genome_t* genome,
                   double position_um[3],
                   nanohole_metrics_t* metrics);

// Verifica métricas de persuasão
int whisper_verify(const nanohole_metrics_t* metrics,
                  const whisper_genome_t* genome);
