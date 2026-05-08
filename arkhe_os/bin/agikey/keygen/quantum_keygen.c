/* bin/agikey/keygen/quantum_keygen.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/agi.h>
#include <linux/quantum_hardware.h>

#define KEY_SIZE_BYTES 32  /* 256-bit key */
#define GENESIS_KEY_PATH "/etc/agi/genesis.key"

struct quantum_keygen_config {
    char *output_path;
    int key_size;
    int backup;
    int verbose;
};

int quantum_keygen_generate(struct quantum_keygen_config *config)
{
    int fd;
    unsigned char key[KEY_SIZE_BYTES];
    unsigned char proof[64];  /* Quantum proof of generation */
    size_t proof_len = sizeof(proof);

    /* Open quantum hardware device */
    fd = open("/dev/agi_rcp", O_RDWR);
    if (fd < 0) {
        if (config->verbose) {
            fprintf(stderr, "Warning: Quantum hardware not available, using classical fallback\n");
        }
        /* Fallback to classical key generation */
        return classical_keygen_generate(config);
    }

    /* Generate quantum genesis key */
    struct agi_identity_args args = {
        .operation = AGI_ID_GENERATE_KEY,
        .key_material = (unsigned long)key,
        .key_len = config->key_size,
        .proof_buffer = (unsigned long)proof,
        .proof_len = proof_len,
    };

    int ret = ioctl(fd, AGI_IOC_IDENTITY, &args);
    close(fd);

    if (ret < 0) {
        fprintf(stderr, "Error: Quantum key generation failed: %s\n", strerror(-ret));
        return -1;
    }

    /* Save key to secure storage */
    if (config->output_path) {
        FILE *f = fopen(config->output_path, "wb");
        if (!f) {
            fprintf(stderr, "Error: Cannot open output file: %s\n", config->output_path);
            return -1;
        }

        /* Write key with metadata header */
        struct key_header {
            uint32_t magic;      /* 0xAG1K3Y */
            uint32_t version;    /* Key format version */
            uint32_t key_size;   /* Key size in bytes */
            uint64_t timestamp;  /* Generation timestamp */
            uint8_t proof[64];   /* Quantum proof of generation */
        } header = {
            .magic = 0x4147314B,  /* "AG1K" */
            .version = 1,
            .key_size = config->key_size,
            .timestamp = time(NULL),
        };
        memcpy(header.proof, proof, sizeof(header.proof));

        fwrite(&header, sizeof(header), 1, f);
        fwrite(key, 1, config->key_size, f);
        fclose(f);

        /* Set secure permissions */
        chmod(config->output_path, 0600);

        if (config->verbose) {
            printf("Genesis key saved to: %s\n", config->output_path);
        }
    }

    /* Create backup if requested */
    if (config->backup && config->output_path) {
        char backup_path[512];
        snprintf(backup_path, sizeof(backup_path), "%s.backup", config->output_path);

        FILE *src = fopen(config->output_path, "rb");
        FILE *dst = fopen(backup_path, "wb");
        if (src && dst) {
            char buffer[4096];
            size_t n;
            while ((n = fread(buffer, 1, sizeof(buffer), src)) > 0) {
                fwrite(buffer, 1, n, dst);
            }
            fclose(src);
            fclose(dst);
            chmod(backup_path, 0600);
            if (config->verbose) {
                printf("Backup created: %s\n", backup_path);
            }
        }
    }

    return 0;
}

int classical_keygen_generate(struct quantum_keygen_config *config)
{
    /* Fallback: generate key using /dev/urandom */
    unsigned char key[KEY_SIZE_BYTES];

    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "Error: Cannot open /dev/urandom\n");
        return -1;
    }

    if (read(fd, key, config->key_size) != (ssize_t)config->key_size) {
        fprintf(stderr, "Error: Failed to read random bytes\n");
        close(fd);
        return -1;
    }
    close(fd);

    /* Save key (same as quantum path, but without quantum proof) */
    if (config->output_path) {
        FILE *f = fopen(config->output_path, "wb");
        if (!f) {
            fprintf(stderr, "Error: Cannot open output file: %s\n", config->output_path);
            return -1;
        }

        /* Write key with classical header */
        struct key_header {
            uint32_t magic;
            uint32_t version;
            uint32_t key_size;
            uint64_t timestamp;
            uint8_t proof[64];  /* Zeroed for classical */
        } header = {
            .magic = 0x4147314B,
            .version = 1,
            .key_size = config->key_size,
            .timestamp = time(NULL),
            .proof = {0},  /* No quantum proof */
        };

        fwrite(&header, sizeof(header), 1, f);
        fwrite(key, 1, config->key_size, f);
        fclose(f);
        chmod(config->output_path, 0600);

        if (config->verbose) {
            printf("Classical genesis key saved to: %s\n", config->output_path);
        }
    }

    return 0;
}