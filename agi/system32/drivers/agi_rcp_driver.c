#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/miscdevice.h>

#define RCP_IOC_TRANSMIT _IOWR('R', 1, struct rcp_transmit_args)
#define RCP_IOC_GET_STATS _IOR('R', 2, struct rcp_stats)

struct rcp_transmit_args {
    char src[32], dst[32];
    unsigned char payload;
    double t_weak, t_post;
    int n_shots;
    unsigned char decoded;
    double fidelity;
};

static long rcp_ioctl(struct file *file, unsigned int cmd, unsigned long arg) {
    return 0;
}

static const struct file_operations rcp_fops = {
    .unlocked_ioctl = rcp_ioctl,
    .owner = THIS_MODULE,
};

static struct miscdevice rcp_misc_dev = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "agi_rcp",
    .fops = &rcp_fops,
};

static int __init agi_rcp_driver_init(void) {
    misc_register(&rcp_misc_dev);
    return 0;
}

static void __exit agi_rcp_driver_exit(void) {
    misc_deregister(&rcp_misc_dev);
}

module_init(agi_rcp_driver_init);
module_exit(agi_rcp_driver_exit);
MODULE_LICENSE("GPL");
