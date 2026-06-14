#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/cdev.h>
#include <linux/slab.h>

#define DEVICE_NAME "cathedral0"
#define RING_BUFFER_SIZE 4096

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Cathedral ARKHE");
MODULE_DESCRIPTION("High-Speed Sensor Ring Buffer for Cathedral Fast Brain");

static int major_num;
static struct cdev cathedral_cdev;
static struct class *cathedral_class;

// Estrutura do dado bruto do sensor (IMU + Timestamp)
struct sensor_payload {
    float accel_x, accel_y, accel_z;
    float gyro_x, gyro_y, gyro_z;
    u64 timestamp_ns;
};

// Ring Buffer lock-free (simplificado para especificação)
static struct sensor_payload ring_buffer[RING_BUFFER_SIZE];
static atomic_t head = ATOMIC_INIT(0);
static atomic_t tail = ATOMIC_INIT(0);

static long cathedral_ioctl(struct file *file, unsigned int cmd, unsigned long arg) {
    struct sensor_payload data_from_user;

    // CMD 1: Injeta dados do sensor no kernel
    if (cmd == 1) {
        if (copy_from_user(&data_from_user, (struct sensor_payload __user *)arg, sizeof(data_from_user))) {
            return -EFAULT;
        }

        int h = atomic_read(&head);
        ring_buffer[h % RING_BUFFER_SIZE] = data_from_user;
        atomic_inc(&head);

        // AQUI: Acorda a thread do Fast Brain (Plano 0) que está bloqueada
        // wake_up_interruptible(&fast_brain_waitqueue);
    }
    return 0;
}

// O Fast Brain em userspace lê isso via read()
static ssize_t cathedral_read(struct file *file, char __user *buf, size_t count, loff_t *ppos) {
    int t = atomic_read(&tail);
    int h = atomic_read(&head);

    if (h == t) return -EAGAIN; // Não há dados novos

    struct sensor_payload data = ring_buffer[t % RING_BUFFER_SIZE];
    atomic_inc(&tail);

    if (copy_to_user(buf, &data, sizeof(data))) return -EFAULT;
    return sizeof(data);
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .read = cathedral_read,
    .unlocked_ioctl = cathedral_ioctl,
};

static int __init cathedral_init(void) {
    alloc_chrdev_region(&major_num, 0, 1, DEVICE_NAME);
    cdev_init(&cathedral_cdev, &fops);
    cdev_add(&cathedral_cdev, major_num, 0);

    cathedral_class = class_create(THIS_MODULE, DEVICE_NAME);
    device_create(cathedral_class, NULL, MKDEV(major_num, 0), NULL, DEVICE_NAME);

    printk(KERN_INFO "Cathedral OS: Kernel Sensor LKM loaded. Device /dev/cathedral0 created.\n");
    return 0;
}

static void __exit cathedral_exit(void) {
    device_destroy(cathedral_class, MKDEV(major_num, 0));
    class_destroy(cathedral_class);
    cdev_del(&cathedral_cdev);
    unregister_chrdev_region(major_num, 0);
    printk(KERN_INFO "Cathedral OS: Kernel Sensor LKM unloaded.\n");
}

module_init(cathedral_init);
module_exit(cathedral_exit);
