#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ARKHE OS");
MODULE_DESCRIPTION("AGI Omni Core Kernel Driver (Substrato 316)");

static int __init agi_omni_kernel_init(void) {
    printk(KERN_INFO "agi_omni_kernel: Inicializando Omni Core Kernel Driver (Substrato 316)...\n");
    return 0;
}

static void __exit agi_omni_kernel_exit(void) {
    printk(KERN_INFO "agi_omni_kernel: Omni Core Kernel Driver descarregado.\n");
}

module_init(agi_omni_kernel_init);
module_exit(agi_omni_kernel_exit);
