/*
 * ARKHE OS Substrato ∞: virtio-9p Server
 * Canon: ∞.Ω.∇+++.∞.bhyve.9p_server
 * Função: Servidor 9p para compartilhamento seguro de dados entre FreeBSD host e Linux guests
 * Linguagem: C (userspace, implements 9p2000.L protocol)
 */

#define _WITH_GETLINE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sha3/sha3.h>
#include <pthread.h>
#include <limits.h>

#define P9_PORT 5640
#define P9_MAX_MSG_SIZE (1024 * 1024)  /* 1MB */
#define SHARED_ROOT "/mnt/arkhe_9p_export"

/* 9p message types */
enum p9_msg_type {
    P9_TLERROR = 6,
    P9_RLERROR = 7,
    P9_TSTATFS = 8,
    P9_RSTATFS = 9,
    P9_TLOPEN = 12,
    P9_RLOPEN = 13,
    P9_TLCREATE = 14,
    P9_RLCREATE = 15,
    P9_TSYMLINK = 16,
    P9_RSYMLINK = 17,
    P9_TMKNOD = 18,
    P9_RMKNOD = 19,
    P9_TRENAME = 20,
    P9_RRENAME = 21,
    P9_TREADLINK = 22,
    P9_RREADLINK = 23,
    P9_TGETATTR = 24,
    P9_RGETATTR = 25,
    P9_TSETATTR = 26,
    P9_RSETATTR = 27,
    P9_TXATTRWALK = 30,
    P9_RXATTRWALK = 31,
    P9_TXATTRCREATE = 32,
    P9_RXATTRCREATE = 33,
    P9_TREADDIR = 40,
    P9_RREADDIR = 41,
    P9_TFSYNC = 50,
    P9_RFSYNC = 51,
    P9_TLOCK = 52,
    P9_RLOCK = 53,
    P9_TGETLOCK = 54,
    P9_RGETLOCK = 55,
    P9_TLINK = 70,
    P9_RLINK = 71,
    P9_TMKDIR = 72,
    P9_RMKDIR = 73,
    P9_TRENAMEAT = 74,
    P9_RRENAMEAT = 75,
    P9_TUNLINKAT = 76,
    P9_RUNLINKAT = 77,
    P9_TVERSION = 100,
    P9_RVERSION = 101,
    P9_TAUTH = 102,
    P9_RAUTH = 103,
    P9_TATTACH = 104,
    P9_RATTACH = 105,
    P9_TERROR = 106,
    P9_RERROR = 107,
    P9_TFLUSH = 108,
    P9_RFLUSH = 109,
    P9_TWALK = 110,
    P9_RWALK = 111,
    P9_TOPEN = 112,
    P9_ROPEN = 113,
    P9_TCREATE = 114,
    P9_RCREATE = 115,
    P9_TSYMLINK_OLD = 116,
    P9_RSYMLINK_OLD = 117,
    P9_TMKNOD_OLD = 118,
    P9_RMKNOD_OLD = 119,
    P9_TREAD = 120,
    P9_RREAD = 121,
    P9_TWRITE = 122,
    P9_RWRITE = 123,
    P9_TCLUNK = 124,
    P9_RCLUNK = 125,
    P9_TREMOVE = 126,
    P9_RREMOVE = 127,
    P9_TSTAT = 128,
    P9_RSTAT = 129,
    P9_TWSTAT = 130,
    P9_RWSTAT = 131,
};

/* Simplified 9p message structure */
struct p9_message {
    uint32_t size;
    uint8_t type;
    uint16_t tag;
    uint8_t payload[];
};

/* File handle for open files */
struct p9_fid {
    int fd;
    char path[512];
    uint32_t flags;
    uint64_t offset;
};

static struct p9_fid *fid_table[1024] = {0};

static int
resolve_arkhe_path(const char *p9_path, char *out_path, size_t out_size)
{
    /* Resolve 9p path relative to ARKHE shared root */
    if (p9_path[0] == '/') {
        snprintf(out_path, out_size, "%s%s", SHARED_ROOT, p9_path);
    } else {
        snprintf(out_path, out_size, "%s/%s", SHARED_ROOT, p9_path);
    }

    /* Security: ensure path stays within shared root */
    char resolved[PATH_MAX];
    if (realpath(out_path, resolved) == NULL) {
        /* Path doesn't exist yet - check parent */
        char *last_slash = strrchr(out_path, '/');
        if (last_slash) {
            *last_slash = '\0';
            if (realpath(out_path, resolved) == NULL) {
                return -1;
            }
            *last_slash = '/';
        } else {
            return -1;
        }
    }

    /* Verify resolved path is under SHARED_ROOT */
    if (strncmp(resolved, SHARED_ROOT, strlen(SHARED_ROOT)) != 0) {
        errno = EACCES;
        return -1;
    }

    strncpy(out_path, resolved, out_size - 1);
    out_path[out_size - 1] = '\0';
    return 0;
}

static int
handle_p9_version(int client_fd, struct p9_message *msg)
{
    /* Parse TVERSION: tag[2] msize[4] version[s] */
    uint16_t tag;
    uint32_t msize;
    char version[256];

    memcpy(&tag, msg->payload, 2);
    memcpy(&msize, msg->payload + 2, 4);

    /* Read version string (p9 string format: length[2] + data) */
    uint16_t vlen;
    memcpy(&vlen, msg->payload + 6, 2);
    if (vlen >= sizeof(version)) vlen = sizeof(version) - 1;
    memcpy(version, msg->payload + 8, vlen);
    version[vlen] = '\0';

    printf("[9p] TVERSION: tag=%d msize=%u version='%s'\n", tag, msize, version);

    /* Send RVERSION: tag[2] msize[4] version[s] */
    char response[512];
    uint32_t resp_size = 7 + 2 + 9;  /* header + msize + "9P2000.L" */
    uint16_t resp_tag = tag;
    uint32_t resp_msize = msize < P9_MAX_MSG_SIZE ? msize : P9_MAX_MSG_SIZE;
    const char *resp_version = "9P2000.L";
    uint16_t resp_vlen = strlen(resp_version);

    memcpy(response, &resp_size, 4);
    response[4] = P9_RVERSION;
    memcpy(response + 5, &resp_tag, 2);
    memcpy(response + 7, &resp_msize, 4);
    memcpy(response + 11, &resp_vlen, 2);
    memcpy(response + 13, resp_version, resp_vlen);

    if (write(client_fd, response, resp_size) != (ssize_t)resp_size) {
        perror("write RVERSION");
        return -1;
    }

    return 0;
}

static int
handle_p9_attach(int client_fd, struct p9_message *msg)
{
    /* Parse TATTACH and respond with success */
    uint16_t tag;
    memcpy(&tag, msg->payload, 2);

    printf("[9p] TATTACH: tag=%d\n", tag);

    /* Send RATTACH: tag[2] qid[13] */
    char response[32] = {0};
    uint32_t resp_size = 20;  /* header + qid */

    memcpy(response, &resp_size, 4);
    response[4] = P9_RATTACH;
    memcpy(response + 5, &tag, 2);

    /* QID: type[1] version[4] path[8] */
    response[7] = 0x80;  /* P9_QTDIR */
    memset(response + 8, 0, 4);  /* version = 0 */
    memset(response + 12, 0, 8);  /* path = 0 (root) */

    if (write(client_fd, response, resp_size) != (ssize_t)resp_size) {
        perror("write RATTACH");
        return -1;
    }

    return 0;
}

static int
handle_p9_walk(int client_fd, struct p9_message *msg)
{
    /* Simplified: always succeed for root walk */
    uint16_t tag;
    memcpy(&tag, msg->payload, 2);

    printf("[9p] TWALK: tag=%d\n", tag);

    /* Send RWALK with success */
    char response[32] = {0};
    uint32_t resp_size = 9;  /* header + nwqid[2] */
    uint16_t nwqid = 0;  /* No walk performed */

    memcpy(response, &resp_size, 4);
    response[4] = P9_RWALK;
    memcpy(response + 5, &tag, 2);
    memcpy(response + 7, &nwqid, 2);

    if (write(client_fd, response, resp_size) != (ssize_t)resp_size) {
        perror("write RWALK");
        return -1;
    }

    return 0;
}

static int
handle_p9_open(int client_fd, struct p9_message *msg)
{
    /* Parse TOPEN: tag[2] fid[4] flags[1] */
    uint16_t tag;
    uint32_t fid;
    uint8_t flags;

    memcpy(&tag, msg->payload, 2);
    memcpy(&fid, msg->payload + 2, 4);
    memcpy(&flags, msg->payload + 6, 1);

    printf("[9p] TOPEN: tag=%d fid=%u flags=0x%x\n", tag, fid, flags);

    /* Map fid to file descriptor */
    if (fid >= 1024 || fid_table[fid] == NULL) {
        /* Send RERROR */
        char response[64];
        const char *err = "fid not valid";
        uint32_t resp_size = 7 + 2 + strlen(err);

        memcpy(response, &resp_size, 4);
        response[4] = P9_RLERROR;
        memcpy(response + 5, &tag, 2);
        uint32_t errno_code = EBADF;
        memcpy(response + 7, &errno_code, 4);
        memcpy(response + 11, err, strlen(err));

        write(client_fd, response, resp_size);
        return -1;
    }

    struct p9_fid *p9fid = fid_table[fid];

    /* Convert 9p flags to open flags */
    int open_flags = 0;
    if (flags & 0x01) open_flags |= O_RDONLY;
    if (flags & 0x02) open_flags |= O_WRONLY;
    if (flags & 0x03) open_flags |= O_RDWR;
    if (flags & 0x40) open_flags |= O_CREAT;
    if (flags & 0x80) open_flags |= O_EXCL;

    /* Re-open file with correct flags */
    int fd = open(p9fid->path, open_flags, 0644);
    if (fd < 0) {
        perror("open");
        /* Send error response */
        return -1;
    }

    /* Update fid */
    if (p9fid->fd >= 0) close(p9fid->fd);
    p9fid->fd = fd;
    p9fid->flags = flags;
    p9fid->offset = 0;

    /* Send RLOPEN: tag[2] qid[13] iounit[4] */
    char response[32] = {0};
    uint32_t resp_size = 24;

    memcpy(response, &resp_size, 4);
    response[4] = P9_RLOPEN;
    memcpy(response + 5, &tag, 2);

    /* QID - reuse from attach */
    response[7] = 0x00;  /* Regular file */
    memset(response + 8, 0, 12);

    /* iounit = 0 (use default) */
    memset(response + 20, 0, 4);

    if (write(client_fd, response, resp_size) != (ssize_t)resp_size) {
        perror("write RLOPEN");
        close(fd);
        return -1;
    }

    return 0;
}

static int
handle_p9_read(int client_fd, struct p9_message *msg)
{
    /* Parse TREAD: tag[2] fid[4] offset[8] count[4] */
    uint16_t tag;
    uint32_t fid, count;
    uint64_t offset;

    memcpy(&tag, msg->payload, 2);
    memcpy(&fid, msg->payload + 2, 4);
    memcpy(&offset, msg->payload + 6, 8);
    memcpy(&count, msg->payload + 14, 4);

    printf("[9p] TREAD: tag=%d fid=%u offset=%lu count=%u\n",
           tag, fid, (unsigned long)offset, count);

    if (fid >= 1024 || fid_table[fid] == NULL || fid_table[fid]->fd < 0) {
        /* Send error */
        return -1;
    }

    struct p9_fid *p9fid = fid_table[fid];

    /* Seek to offset */
    if (lseek(p9fid->fd, offset, SEEK_SET) < 0) {
        perror("lseek");
        return -1;
    }

    /* Read data */
    char *buf = malloc(count);
    if (!buf) return -1;

    ssize_t nread = read(p9fid->fd, buf, count);
    if (nread < 0) {
        perror("read");
        free(buf);
        return -1;
    }

    /* Send RREAD: tag[2] count[4] data[count] */
    uint32_t resp_size = 7 + 4 + nread;
    char *response = malloc(resp_size);
    if (!response) {
        free(buf);
        return -1;
    }

    memcpy(response, &resp_size, 4);
    response[4] = P9_RREAD;
    memcpy(response + 5, &tag, 2);
    memcpy(response + 7, &nread, 4);
    memcpy(response + 11, buf, nread);

    if (write(client_fd, response, resp_size) != resp_size) {
        perror("write RREAD");
    }

    free(buf);
    free(response);
    return 0;
}

static void *
p9_server_thread(void *arg)
{
    int server_fd = *(int *)arg;
    free(arg);

    char buffer[P9_MAX_MSG_SIZE];

    while (1) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            continue;
        }

        printf("[9p] Client connected: fd=%d\n", client_fd);

        /* Handle 9p messages */
        while (1) {
            /* Read message header: size[4] */
            uint32_t msg_size;
            if (read(client_fd, &msg_size, 4) != 4) break;

            if (msg_size > P9_MAX_MSG_SIZE || msg_size < 7) {
                fprintf(stderr, "Invalid message size: %u\n", msg_size);
                break;
            }

            /* Read rest of message */
            if (read(client_fd, buffer + 4, msg_size - 4) != (ssize_t)(msg_size - 4)) {
                break;
            }

            struct p9_message *msg = (struct p9_message *)buffer;

            /* Dispatch by message type */
            switch (msg->type) {
                case P9_TVERSION:
                    handle_p9_version(client_fd, msg);
                    break;
                case P9_TATTACH:
                    handle_p9_attach(client_fd, msg);
                    break;
                case P9_TWALK:
                    handle_p9_walk(client_fd, msg);
                    break;
                case P9_TOPEN:
                    handle_p9_open(client_fd, msg);
                    break;
                case P9_TREAD:
                    handle_p9_read(client_fd, msg);
                    break;
                case P9_TCLUNK:
                    /* Simplified: just acknowledge */
                    {
                        uint16_t tag;
                        memcpy(&tag, msg->payload, 2);
                        char resp[9] = {0};
                        uint32_t resp_size = 9;
                        memcpy(resp, &resp_size, 4);
                        resp[4] = P9_RCLUNK;
                        memcpy(resp + 5, &tag, 2);
                        write(client_fd, resp, 9);
                    }
                    break;
                default:
                    fprintf(stderr, "Unhandled 9p message type: %d\n", msg->type);
                    /* Send error response */
                    break;
            }
        }

        /* Cleanup fids for this client */
        for (int i = 0; i < 1024; i++) {
            if (fid_table[i]) {
                if (fid_table[i]->fd >= 0) close(fid_table[i]->fd);
                free(fid_table[i]);
                fid_table[i] = NULL;
            }
        }

        close(client_fd);
        printf("[9p] Client disconnected\n");
    }

    return NULL;
}

int
main(int argc, char *argv[])
{
    int server_fd;
    struct sockaddr_in addr;

    /* Create server socket */
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return 1;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");  /* Only localhost */
    addr.sin_port = htons(P9_PORT);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    if (listen(server_fd, 5) < 0) {
        perror("listen");
        return 1;
    }

    printf("[9p] Server listening on 127.0.0.1:%d\n", P9_PORT);
    printf("[9p] Shared root: %s\n", SHARED_ROOT);

    /* Start server thread */
    pthread_t server_thread;
    int *fd_ptr = malloc(sizeof(int));
    *fd_ptr = server_fd;

    if (pthread_create(&server_thread, NULL, p9_server_thread, fd_ptr) != 0) {
        perror("pthread_create");
        return 1;
    }

    /* Main thread waits */
    pthread_join(server_thread, NULL);

    close(server_fd);
    return 0;
}
