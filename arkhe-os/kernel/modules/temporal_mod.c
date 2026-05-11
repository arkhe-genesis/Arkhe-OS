/*
 * ARKHE Ω-TEMP — Módulo Kernel: Cadeia Temporal
 *
 * Implementa a Temporal Hash Chain diretamente no kernel space
 * para máxima performance e integração com o subsistema de rede.
 *
 * A cadeia temporal é armazenada em memória kernel usando uma
 * estrutura otimizada com cache-friendly layout.
 *
 * Operações:
 *   - Inserção de blocos (append-only)
 *   - Validação de integridade (hash chain)
 *   - Busca por índice ou hash
 *   - Iteração temporal (forward/backward)
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/rwlock.h>
#include <linux/kref.h>
#include <linux/crypto.h>
#include <linux/scatterlist.h>
#include <crypto/hash.h>

#include "arkhe_temporal.h"

#define ARKHE_TEMPORAL_DEVICE_NAME "arkhe-temporal"
#define ARKHE_TEMPORAL_CLASS_NAME  "arkhe"

/*
 * Estrutura de um bloco temporal no kernel
 */
struct arkhe_temporal_block {
    u64         index;
    u8          prev_hash[ARKHE_HASH_SIZE];   /* SHA3-256 do bloco anterior */
    u64         timestamp;                    /* Nanossegundos desde boot */
    u32         msg_count;
    u8          state_root[ARKHE_HASH_SIZE];  /* Merkle root do estado */
    u8          oracle_root[ARKHE_HASH_SIZE]; /* Root da avaliação do Oracle */
    u32         payload_size;
    void        *payload;                     /* Dados das mensagens */
    u8          block_hash[ARKHE_HASH_SIZE];  /* Hash deste bloco */

    /* List linking */
    struct list_head chain;
    struct hlist_node hash_node;
};

/*
 * Cadeia temporal principal
 */
struct arkhe_temporal_chain {
    spinlock_t          lock;
    struct list_head    blocks;            /* Lista ordenada por índice */
    struct hlist_head   *hash_table;       /* Hash table para busca O(1) */
    u64                 length;
    u64                 max_length;
    struct arkhe_temporal_block *genesis;
    u8                  chain_state_root[ARKHE_HASH_SIZE];
};

/*
 * Bloco gênesis — o primeiro bloco da cadeia, criado na inicialização.
 * Todos os blocos subsequentes derivam causalmente deste.
 */
static const u8 genesis_payload[] = {
    'A', 'R', 'K', 'H', 'E', ' ',
    'G', 'E', 'N', 'E', 'S', 'I', 'S',
    ' ', 'B', 'L', 'O', 'C', 'K',
    ' ', 'O', 'M', 'E', 'G', 'A', '-',
    'T', 'E', 'M', 'P', '-', 'V', '4', '.', '3', '.', '7',
};

/* Dispositivo de caractere */
static dev_t           arkhe_dev;
static struct cdev      arkhe_cdev;
static struct class    *arkhe_class;
static struct device   *arkhe_device;

/* Cadeia global */
static struct arkhe_temporal_chain *global_chain;

/* ============================================================================
 * SHA3-256 via Crypto API do kernel
 * ============================================================================

static int kernel_sha3_256(const u8 *data, size_t len, u8 *digest)
{
    struct crypto_shash *tfm;
    struct shash_desc   *desc;
    int                  ret;
    size_t               desc_size;

    tfm = crypto_alloc_shash("sha3-256", 0, 0);
    if (IS_ERR(tfm))
        return PTR_ERR(tfm);

    desc_size = crypto_shash_descsize(tfm) + sizeof(*desc);
    desc = kmalloc(desc_size, GFP_KERNEL);
    if (!desc) {
        crypto_free_shash(tfm);
        return -ENOMEM;
    }

    desc->tfm = tfm;
    desc->flags = 0;

    ret = crypto_shash_init(desc);
    if (ret)
        goto out;

    ret = crypto_shash_update(desc, data, len);
    if (ret)
        goto out;

    ret = crypto_shash_final(desc, digest);

out:
    kfree(desc);
    crypto_free_shash(tfm);
    return ret;
}

/* ============================================================================
 * Merkle Tree Root (kernel-optimized)
 * ============================================================================

static int compute_merkle_root(u8 *leaves, u32 num_leaves, u8 *root)
{
    u8    *level, *next_level;
    u32    level_count, next_count;
    u32    i;
    u8    *buf;
    int    ret;

    if (num_leaves == 0) {
        /* Raiz de árvore vazia = hash vazio */
        return kernel_sha3_256(NULL, 0, root);
    }

    /* Alocar buffer para dois níveis */
    level = kmalloc_array(num_leaves, ARKHE_HASH_SIZE, GFP_KERNEL);
    if (!level)
        return -ENOMEM;

    next_level = kmalloc_array(num_leaves, ARKHE_HASH_SIZE, GFP_KERNEL);
    if (!next_level) {
        kfree(level);
        return -ENOMEM;
    }

    /* Copiar folhas */
    memcpy(level, leaves, num_leaves * ARKHE_HASH_SIZE);
    level_count = num_leaves;

    while (level_count > 1) {
        next_count = 0;

        for (i = 0; i < level_count; i += 2) {
            if (i + 1 < level_count) {
                /* Hash de dois nós */
                buf = kmalloc(ARKHE_HASH_SIZE * 2, GFP_KERNEL);
                if (!buf) {
                    kfree(level);
                    kfree(next_level);
                    return -ENOMEM;
                }
                memcpy(buf, &level[i * ARKHE_HASH_SIZE], ARKHE_HASH_SIZE);
                memcpy(&buf[ARKHE_HASH_SIZE],
                       &level[(i + 1) * ARKHE_HASH_SIZE],
                       ARKHE_HASH_SIZE);

                ret = kernel_sha3_256(buf, ARKHE_HASH_SIZE * 2,
                                       &next_level[next_count * ARKHE_HASH_SIZE]);
                kfree(buf);
                if (ret) {
                    kfree(level);
                    kfree(next_level);
                    return ret;
                }
            } else {
                /* Nó ímpar: duplica */
                memcpy(&next_level[next_count * ARKHE_HASH_SIZE],
                       &level[i * ARKHE_HASH_SIZE],
                       ARKHE_HASH_SIZE);
            }
            next_count++;
        }

        /* Trocar níveis */
        memcpy(level, next_level, next_count * ARKHE_HASH_SIZE);
        level_count = next_count;
    }

    memcpy(root, level, ARKHE_HASH_SIZE);

    kfree(level);
    kfree(next_level);
    return 0;
}

/* ============================================================================
 * Validação de Bloco Temporal
 * ============================================================================

static int validate_temporal_block(struct arkhe_temporal_block *block,
                                    struct arkhe_temporal_block *prev)
{
    u8 computed_hash[ARKHE_HASH_SIZE];
    u8 merkle_root[ARKHE_HASH_SIZE];
    int ret;

    /* 1. Verificar índice */
    if (prev && block->index != prev->index + 1) {
        pr_err("ARKHE: índice inválido: esperado %llu, obtido %llu\n",
               prev->index + 1, block->index);
        return -EINVAL;
    }

    /* 2. Verificar prev_hash */
    if (prev) {
        if (memcmp(block->prev_hash, prev->block_hash, ARKHE_HASH_SIZE) != 0) {
            pr_err("ARKHE: prev_hash não confere no bloco %llu\n",
                   block->index);
            return -EINVAL;
        }
    } else if (block->index != 0) {
        /* Bloco 0 deve ser gênesis */
        pr_err("ARKHE: bloco 0 não é gênesis mas não tem prev\n");
        return -EINVAL;
    }

    /* 3. Verificar timestamp */
    if (prev && block->timestamp <= prev->timestamp) {
        pr_err("ARKHE: timestamp não-causal no bloco %llu\n",
               block->index);
        return -EINVAL;
    }

    /* 4. Verificar Merkle root */
    if (block->msg_count > 0 && block->payload) {
        ret = compute_merkle_root(block->payload, block->msg_count,
                                  merkle_root);
        if (ret)
            return ret;

        if (memcmp(block->state_root, merkle_root, ARKHE_HASH_SIZE) != 0) {
            pr_err("ARKHE: Merkle root inválido no bloco %llu\n",
                   block->index);
            return -EINVAL;
        }
    }

    /* 5. Verificar hash do bloco */
    ret = kernel_sha3_256(block, sizeof(struct arkhe_temporal_block) - ARKHE_HASH_SIZE,
                   computed_hash);
    if (ret)
        return ret;

    if (memcmp(block->block_hash, computed_hash, ARKHE_HASH_SIZE) != 0) {
        pr_err("ARKHE: block_hash inválido no bloco %llu\n",
               block->index);
        return -EINVAL;
    }

    return 0;
}

/* ============================================================================
 * Inserção de Bloco
 * ============================================================================

static int temporal_insert_block(struct arkhe_temporal_block *new_block)
{
    struct arkhe_temporal_chain *chain = global_chain;
    struct arkhe_temporal_block *last = NULL;
    unsigned long flags;
    int ret;

    spin_lock_irqsave(&chain->lock, flags);

    /* Obter último bloco */
    if (!list_empty(&chain->blocks)) {
        last = list_last_entry(&chain->blocks,
                               struct arkhe_temporal_block, chain);
    }

    /* Validar */
    ret = validate_temporal_block(new_block, last);
    if (ret) {
        spin_unlock_irqrestore(&chain->lock, flags);
        return ret;
    }

    /* Adicionar à lista */
    list_add_tail(&new_block->chain, &chain->blocks);

    /* Adicionar à hash table */
    u32 hash_idx = hash_min(new_block->block_hash, ARKHE_HASH_TABLE_BITS);
    hlist_add_head(&new_block->hash_node, &chain->hash_table[hash_idx]);

    chain->length++;

    /* Atualizar state root global */
    memcpy(chain->chain_state_root, new_block->state_root,
           ARKHE_HASH_SIZE);

    spin_unlock_irqrestore(&chain->lock, flags);

    pr_info("ARKHE: Bloco %llu inserido (hash=%*pE)\n",
            new_block->index, ARKHE_HASH_SIZE, new_block->block_hash);

    /* Notificar espaço userspace */
    /* ... (via uevent ou netlink) */

    return 0;
}

/* ============================================================================
 * File Operations — /dev/arkhe/temporal
 * ============================================================================

static ssize_t temporal_write(struct file *filp, const char __user *buf,
                              size_t len, loff_t *ppos)
{
    struct arkhe_temporal_block *block;
    int ret;

    /* Limitar tamanho máximo de bloco */
    if (len > ARKHE_MAX_BLOCK_SIZE) {
        pr_warn("ARKHE: bloco muito grande (%zu bytes)\n", len);
        return -EFBIG;
    }

    /* Alocar bloco */
    block = kzalloc(sizeof(*block) + len, GFP_KERNEL);
    if (!block)
        return -ENOMEM;

    /* Copiar dados do userspace */
    if (copy_from_user(block->payload, buf, len)) {
        kfree(block);
        return -EFAULT;
    }

    block->payload_size = len;
    block->timestamp = ktime_get_real_ns();

    /* Computar hash */
    ret = kernel_sha3_256(block->payload, len, block->state_root);
    if (ret) {
        kfree(block);
        return ret;
    }

    /* Tentar inserir */
    ret = temporal_insert_block(block);
    if (ret) {
        kfree(block);
        return ret;
    }

    return len;
}

static ssize_t temporal_read(struct file *filp, char __user *buf,
                             size_t len, loff_t *ppos)
{
    struct arkhe_temporal_chain *chain = global_chain;
    struct arkhe_temporal_block *block;
    unsigned long flags;
    u64 idx = *ppos;
    ssize_t copied = 0;

    spin_lock_irqsave(&chain->lock, flags);

    /* Encontrar bloco pelo índice */
    list_for_each_entry(block, &chain->blocks, chain) {
        if (block->index == idx) {
            size_t block_size = sizeof(*block) + block->payload_size;
            size_t to_copy = min(len, block_size);

            if (copy_to_user(buf, block, to_copy)) {
                spin_unlock_irqrestore(&chain->lock, flags);
                return -EFAULT;
            }

            copied = to_copy;
            *ppos = idx + 1;
            break;
        }
    }

    spin_unlock_irqrestore(&chain->lock, flags);
    return copied;
}

static int temporal_open(struct inode *inode, struct file *filp)
{
    /* Incrementar refcount do módulo */
    try_module_get(THIS_MODULE);
    return 0;
}

static int temporal_release(struct inode *inode, struct file *filp)
{
    module_put(THIS_MODULE);
    return 0;
}

static loff_t temporal_llseek(struct file *filp, loff_t offset, int whence)
{
    struct arkhe_temporal_chain *chain = global_chain;

    switch (whence) {
    case SEEK_SET:
        break;
    case SEEK_CUR:
        offset = filp->f_pos + offset;
        break;
    case SEEK_END:
        offset = chain->length + offset;
        break;
    default:
        return -EINVAL;
    }

    if (offset < 0 || offset > chain->length)
        return -EINVAL;

    filp->f_pos = offset;
    return offset;
}

/* Ioctl commands */
#define ARKHE_TEMPORAL_GET_LENGTH  _IOR('a', 0, u64)
#define ARKHE_TEMPORAL_GET_ROOT   _IOWR('a', 1, u8[32])
#define ARKHE_TEMPORAL_GET_BLOCK  _IOWR('a', 2, struct arkhe_block_query)

static long temporal_ioctl(struct file *filp, unsigned int cmd,
                           unsigned long arg)
{
    struct arkhe_temporal_chain *chain = global_chain;
    void __user *argp = (void __user *)arg;
    int ret = 0;

    switch (cmd) {
    case ARKHE_TEMPORAL_GET_LENGTH: {
        u64 len;
        spin_lock(&chain->lock);
        len = chain->length;
        spin_unlock(&chain->lock);
        if (copy_to_user(argp, &len, sizeof(len)))
            return -EFAULT;
        break;
    }

    case ARKHE_TEMPORAL_GET_ROOT: {
        u8 root[ARKHE_HASH_SIZE];
        spin_lock(&chain->lock);
        memcpy(root, chain->chain_state_root, ARKHE_HASH_SIZE);
        spin_unlock(&chain->lock);
        if (copy_to_user(argp, root, ARKHE_HASH_SIZE))
            return -EFAULT;
        break;
    }

    default:
        ret = -ENOTTY;
    }

    return ret;
}

static const struct file_operations temporal_fops = {
    .owner          = THIS_MODULE,
    .open           = temporal_open,
    .release        = temporal_release,
    .read           = temporal_read,
    .write          = temporal_write,
    .llseek         = temporal_llseek,
    .unlocked_ioctl = temporal_ioctl,
};

/* ============================================================================
 * Network Filter — Netfilter Hook ARKHE
 * ============================================================================

static struct nf_hook_ops arkhe_nf_ops;

static unsigned int arkhe_netfilter(void *priv,
                                     struct sk_buff *skb,
                                     const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct arkhe_header *arkhe_hdr;

    if (!skb)
        return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (!iph)
        return NF_ACCEPT;

    /* Verificar se é tráfego ARKHE (protocolo IP proprietário 253) */
    if (iph->protocol != IPPROTO_ARKHE)
        return NF_ACCEPT;

    arkhe_hdr = (struct arkhe_header *)(skb->data + iph->ihl * 4);

    /* Verificar magic number */
    if (arkhe_hdr->magic != htons(ARKHE_MAGIC))
        return NF_DROP;

    /* Verificar versão */
    if (arkhe_hdr->version != ARKHE_VERSION) {
        pr_warn("ARKHE: versão incompatível: %u\n",
                arkhe_hdr->version);
        return NF_DROP;
    }

    /* Verificar checksum */
    if (arkhe_hdr->checksum != arkhe_compute_checksum(arkhe_hdr)) {
        pr_warn("ARKHE: checksum inválido\n");
        return NF_DROP;
    }

    /* Passar para o módulo de consenso */
    return arkhe_consensus_process(arkhe_hdr, skb);
}

/* ============================================================================
 * Inicialização do Módulo
 * ============================================================================

static int __init arkhe_temporal_init(void)
{
    int ret;

    pr_info("ARKHE Ω-TEMP: Inicializando módulo temporal\n");

    /* Alocar device number */
    ret = alloc_chrdev_region(&arkhe_dev, 0, 1,
                              ARKHE_TEMPORAL_DEVICE_NAME);
    if (ret < 0) {
        pr_err("ARKHE: falha ao alocar device number\n");
        return ret;
    }

    /* Criar classe de dispositivo */
    arkhe_class = class_create(THIS_MODULE,
                                ARKHE_TEMPORAL_CLASS_NAME);
    if (IS_ERR(arkhe_class)) {
        ret = PTR_ERR(arkhe_class);
        goto err_class;
    }

    /* Criar dispositivo */
    arkhe_device = device_create(arkhe_class, NULL, arkhe_dev,
                                  NULL, ARKHE_TEMPORAL_DEVICE_NAME);
    if (IS_ERR(arkhe_device)) {
        ret = PTR_ERR(arkhe_device);
        goto err_device;
    }

    /* Inicializar character device */
    cdev_init(&arkhe_cdev, &temporal_fops);
    ret = cdev_add(&arkhe_cdev, arkhe_dev, 1);
    if (ret)
        goto err_cdev;

    /* Alocar cadeia temporal */
    global_chain = kzalloc(sizeof(*global_chain), GFP_KERNEL);
    if (!global_chain) {
        ret = -ENOMEM;
        goto err_chain;
    }

    spin_lock_init(&global_chain->lock);
    INIT_LIST_HEAD(&global_chain->blocks);
    global_chain->max_length = ARKHE_MAX_BLOCKS;

    /* Alocar hash table */
    global_chain->hash_table = kzalloc(
        sizeof(struct hlist_head) * ARKHE_HASH_TABLE_SIZE, GFP_KERNEL);
    if (!global_chain->hash_table) {
        ret = -ENOMEM;
        goto err_hashtable;
    }

    /* Criar bloco gênesis */
    struct arkhe_temporal_block *genesis = kzalloc(
        sizeof(*genesis) + sizeof(genesis_payload), GFP_KERNEL);
    if (!genesis) {
        ret = -ENOMEM;
        goto err_genesis;
    }

    genesis->index = 0;
    genesis->timestamp = ktime_get_real_ns();
    genesis->msg_count = 1;
    genesis->payload_size = sizeof(genesis_payload);
    memcpy(genesis->payload, genesis_payload, sizeof(genesis_payload));

    /* Hash do genesis: SHA3-256(payload) */
    kernel_sha3_256(genesis_payload, sizeof(genesis_payload),
                    genesis->state_root);

    /* prev_hash = zeros */
    memset(genesis->prev_hash, 0, ARKHE_HASH_SIZE);

    /* Hash do bloco */
    kernel_sha3_256(genesis, sizeof(*genesis) + sizeof(genesis_payload),
                    genesis->block_hash);

    genesis->block_hash[0] = 0xCA;  /* Marker: 0xCA71 = Cathedral */
    genesis->block_hash[1] = 0x71;

    global_chain->genesis = genesis;

    /* Inserir genesis na lista (sem validação) */
    list_add(&genesis->chain, &global_chain->blocks);
    hlist_add_head(&genesis->hash_node,
                   &global_chain->hash_table[0]);
    global_chain->length = 1;

    memcpy(global_chain->chain_state_root, genesis->state_root,
           ARKHE_HASH_SIZE);

    pr_info("ARKHE: Módulo temporal carregado — Genesis Block criado\n");
    pr_info("ARKHE: Chain state root: %*pE\n",
            ARKHE_HASH_SIZE, genesis->state_root);

    return 0;

err_genesis:
    kfree(global_chain->hash_table);
err_hashtable:
    kfree(global_chain);
err_chain:
    cdev_del(&arkhe_cdev);
err_cdev:
    device_destroy(arkhe_class, arkhe_dev);
err_device:
    class_destroy(arkhe_class);
err_class:
    unregister_chrdev_region(arkhe_dev, 1);
    return ret;
}

static void __exit arkhe_temporal_exit(void)
{
    struct arkhe_temporal_block *block, *tmp;

    pr_info("ARKHE: Encerrando módulo temporal\n");

    /* Remover blocos */
    list_for_each_entry_safe(block, tmp, &global_chain->blocks, chain) {
        list_del(&block->chain);
        hlist_del(&block->hash_node);
        kfree(block->payload);
        kfree(block);
    }

    kfree(global_chain->hash_table);
    kfree(global_chain);

    cdev_del(&arkhe_cdev);
    device_destroy(arkhe_class, arkhe_dev);
    class_destroy(arkhe_class);
    unregister_chrdev_region(arkhe_dev, 1);

    pr_info("ARKHE: Módulo temporal encerrado\n");
}

module_init(arkhe_temporal_init);
module_exit(arkhe_temporal_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ARKHE CATHEDRAL");
MODULE_DESCRIPTION("ARKHE Ω-TEMP — Temporal Hash Chain (Kernel Module)");
MODULE_VERSION("4.3.7");
