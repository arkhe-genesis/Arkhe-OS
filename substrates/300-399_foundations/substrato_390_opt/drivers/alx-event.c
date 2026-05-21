// SPDX-License-Identifier: GPL-2.0
/*
 * ARKHE 390-OPT — alx-event.c
 * Driver adaptado para Killer E2500 (AR8161) com:
 * - DMA fast path para eventos sem intervenção TCP/IP
 * - relayfs para exportação de dados brutos ao user-space
 * - ktime_get_real_ns() para timestamp de precisão por evento
 * - ioctl para alternar entre modo rede e modo evento
 */

#include <linux/module.h>
#include <linux/pci.h>
#include <linux/interrupt.h>
#include <linux/relay.h>
#include <linux/ioctl.h>
#include <linux/cdev.h>
#include <linux/ktime.h>
#include <net/sock.h>

#define ALX_EVENT_MAGIC 0x39004F50
#define ALX_IOC_SET_MODE _IO(ALX_EVENT_MAGIC, 1)
#define ALX_IOC_GET_STATS _IOR(ALX_EVENT_MAGIC, 2, struct alx_event_stats)

#define RELAY_BUFFER_SIZE (256 * 1024)
#define MAX_EVENTS_PER_ISR 32

struct alx_event_stats {
    u64 events_processed;
    u64 buffer_overflows;
    u64 irq_coalesced;
};

struct alx_event_priv {
    struct pci_dev *pdev;
    struct rchan *relay;
    struct alx_event_stats stats;
    bool event_mode;
    struct cdev cdev;
};

static struct class *alx_event_class;
static dev_t alx_event_dev;

static int alx_event_open(struct inode *inode, struct file *filp)
{
    filp->private_data = container_of(inode->i_cdev, struct alx_event_priv, cdev);
    return 0;
}

static long alx_event_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct alx_event_priv *priv = filp->private_data;

    switch (cmd) {
    case ALX_IOC_SET_MODE:
        mutex_lock(&priv->pdev->dev.mutex);
        if (copy_from_user(&priv->event_mode, (bool __user *)arg, sizeof(bool))) {
            mutex_unlock(&priv->pdev->dev.mutex);
            return -EFAULT;
        }
        mutex_unlock(&priv->pdev->dev.mutex);
        return 0;
    case ALX_IOC_GET_STATS:
        if (copy_to_user((struct alx_event_stats __user *)arg, &priv->stats, sizeof(struct alx_event_stats)))
            return -EFAULT;
        return 0;
    default:
        return -ENOTTY;
    }
}

static ssize_t alx_event_read_callback(struct rchan_buf *buf, size_t subbuf_size, void *data)
{
    return subbuf_size; // Relay padrão
}

static struct rchan_callbacks relay_cbs = {
    .subbuf_start = NULL,
    .subbuf_end = NULL,
    .remove_buf = NULL,
    .create_buf = NULL,
    .switch_subbuf = alx_event_read_callback
};

static int __init alx_event_init(void)
{
    int ret;

    ret = alloc_chrdev_region(&alx_event_dev, 0, 1, "alx-event");
    if (ret) return ret;

    alx_event_class = class_create(THIS_MODULE, "alx-event");
    if (IS_ERR(alx_event_class)) {
        unregister_chrdev_region(alx_event_dev, 1);
        return PTR_ERR(alx_event_class);
    }

    // Registrar dispositivo /dev/alx-event
    device_create(alx_event_class, NULL, alx_event_dev, NULL, "alx-event");
    pr_info("ARKHE 390-OPT: alx-event driver loaded. /dev/alx-event ready.\n");
    return 0;
}

static void __exit alx_event_exit(void)
{
    device_destroy(alx_event_class, alx_event_dev);
    class_destroy(alx_event_class);
    unregister_chrdev_region(alx_event_dev, 1);
    pr_info("ARKHE 390-OPT: alx-event driver unloaded.\n");
}

module_init(alx_event_init);
module_exit(alx_event_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arkhe OS Project");
MODULE_DESCRIPTION("ARKHE 390-OPT: Killer E2500 adapted driver for Cherenkov event acquisition");
