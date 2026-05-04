/* arkhe.c — Módulo de kernel ARKHE para Linux
 * Integra o Sidecar e o Inquisidor no espaço do kernel
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/sched.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

#define ARKHE_MAJOR 250
#define ARKHE_NAME "arkhe"
#define ARKHE_CLASS "arkhe"

/* Estado global da Catedral no kernel */
struct arkhe_state {
    long coherence;         /* r(t) * 1000 */
    long global_phase;      /* ψ(t) * 1000 */
    unsigned long events_processed;
    unsigned long events_blocked;
    unsigned long events_hesitated;
};

static struct arkhe_state arkhe = {
    .coherence = 850,
    .global_phase = 0,
    .events_processed = 0,
    .events_blocked = 0,
    .events_hesitated = 0,
};

static dev_t arkhe_dev;
static struct cdev arkhe_cdev;
static struct class *arkhe_class;

/* IOCTL interface */
#define ARKHE_MAGIC 'A'
#define ARKHE_QUERY_STATUS  _IOR(ARKHE_MAGIC, 0, struct arkhe_state)
#define ARKHE_SUBMIT_EVENT  _IOWR(ARKHE_MAGIC, 1, struct arkhe_event)
#define ARKHE_SET_COHERENCE _IOW(ARKHE_MAGIC, 2, long)

struct arkhe_event {
    char payload[256];
    int payload_len;
    int verdict; /* 0=ALLOW, 1=DENY, 2=HESITATE */
};

/* Sidecar em kernel space */
static int arkhe_sidecar_check(const char *payload, int len)
{
    int i;

    /* Runa Proibida: byte nulo */
    for (i = 0; i < len; i++) {
        if (payload[i] == 0x00) {
            arkhe.events_blocked++;
            return 1; /* DENY */
        }
    }

    /* Endereço fixo */
    for (i = 0; i < len - 2; i++) {
        if (payload[i] == '0' && payload[i+1] == 'x') {
            int hex_count = 0;
            int j;
            for (j = i + 2; j < min(i + 18, (int)len); j++) {
                char c = payload[j];
                if ((c >= '0' && c <= '9') ||
                    (c >= 'a' && c <= 'f') ||
                    (c >= 'A' && c <= 'F')) {
                    hex_count++;
                } else {
                    break;
                }
            }
            if (hex_count >= 8) {
                arkhe.events_blocked++;
                return 1; /* DENY */
            }
        }
    }

    return 0; /* ALLOW */
}

static long arkhe_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct arkhe_event event;

    switch (cmd) {
    case ARKHE_QUERY_STATUS:
        if (copy_to_user((void __user *)arg, &arkhe, sizeof(arkhe)))
            return -EFAULT;
        return 0;

    case ARKHE_SUBMIT_EVENT:
        if (copy_from_user(&event, (void __user *)arg, sizeof(event)))
            return -EFAULT;

        arkhe.events_processed++;
        event.verdict = arkhe_sidecar_check(event.payload, event.payload_len);

        if (copy_to_user((void __user *)arg, &event, sizeof(event)))
            return -EFAULT;
        return 0;

    case ARKHE_SET_COHERENCE:
        if (copy_from_user(&arkhe.coherence, (void __user *)arg, sizeof(long)))
            return -EFAULT;
        return 0;

    default:
        return -EINVAL;
    }
}

static int arkhe_open(struct inode *inode, struct file *filp)
{
    return 0;
}

static int arkhe_release(struct inode *inode, struct file *filp)
{
    return 0;
}

static const struct file_operations arkhe_fops = {
    .owner = THIS_MODULE,
    .open = arkhe_open,
    .release = arkhe_release,
    .unlocked_ioctl = arkhe_ioctl,
};

static int __init arkhe_module_init(void)
{
    int ret;

    pr_info("ARKHE: A Catedral desperta no kernel\n");
    pr_info("ARKHE: Inicializando Muralha de Quartzo...\n");

    /* Alocar device number */
    ret = alloc_chrdev_region(&arkhe_dev, 0, 1, ARKHE_NAME);
    if (ret) {
        pr_err("ARKHE: Falha ao alocar device number\n");
        return ret;
    }

    /* Inicializar cdev */
    cdev_init(&arkhe_cdev, &arkhe_fops);
    arkhe_cdev.owner = THIS_MODULE;
    ret = cdev_add(&arkhe_cdev, arkhe_dev, 1);
    if (ret) {
        unregister_chrdev_region(arkhe_dev, 1);
        return ret;
    }

    /* Criar classe */
    arkhe_class = class_create(ARKHE_CLASS);
    if (IS_ERR(arkhe_class)) {
        cdev_del(&arkhe_cdev);
        unregister_chrdev_region(arkhe_dev, 1);
        return PTR_ERR(arkhe_class);
    }

    /* Criar device */
    device_create(arkhe_class, NULL, arkhe_dev, NULL, ARKHE_NAME);

    pr_info("ARKHE: Device /dev/arkhe criado (major=%d)\n", MAJOR(arkhe_dev));
    pr_info("ARKHE: Muralha ativa. O Inquisidor vigia.\n");

    return 0;
}

static void __exit arkhe_module_exit(void)
{
    device_destroy(arkhe_class, arkhe_dev);
    class_destroy(arkhe_class);
    cdev_del(&arkhe_cdev);
    unregister_chrdev_region(arkhe_dev, 1);

    pr_info("ARKHE: A Catedral adormece. A Muralha cai.\n");
}

module_init(arkhe_module_init);
module_exit(arkhe_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("O Ferreiro");
MODULE_DESCRIPTION("ARKHE System Guardian — A Muralha de Quartzo no Kernel Linux");
MODULE_VERSION("1.0.604");
