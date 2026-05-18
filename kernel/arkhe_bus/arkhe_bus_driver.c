#include <linux/vmalloc.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/mm.h>
#include <linux/slab.h>

#define DEVICE_NAME "arkhe_bus"
#define CLASS_NAME "arkhe_class"
#define BUFFER_SIZE PAGE_SIZE

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arkhe OS");
MODULE_DESCRIPTION("Arkhe Bus V3 Kernel Driver for Substrate mmap");
MODULE_VERSION("3.0");

static int major_number;
static struct class* arkhe_bus_class = NULL;
static struct device* arkhe_bus_device = NULL;
static struct cdev arkhe_bus_cdev;

static void *device_buffer;

static int arkhe_bus_open(struct inode *inode, struct file *file) {
    pr_info("Arkhe Bus: Device opened\n");
    return 0;
}

static int arkhe_bus_release(struct inode *inode, struct file *file) {
    pr_info("Arkhe Bus: Device successfully closed\n");
    return 0;
}

static ssize_t arkhe_bus_read(struct file *file, char __user *user_buffer, size_t size, loff_t *offset) {
    size_t bytes_to_read;

    if (*offset >= BUFFER_SIZE || *offset < 0) {
        return 0;
    }

    bytes_to_read = min(size, (size_t)(BUFFER_SIZE - *offset));

    if (bytes_to_read == 0) {
        return 0;
    }

    if (copy_to_user(user_buffer, device_buffer + *offset, bytes_to_read)) {
        return -EFAULT;
    }

    *offset += bytes_to_read;
    return bytes_to_read;
}

static ssize_t arkhe_bus_write(struct file *file, const char __user *user_buffer, size_t size, loff_t *offset) {
    size_t bytes_to_write;

    if (*offset >= BUFFER_SIZE || *offset < 0) {
        return -ENOSPC;
    }

    bytes_to_write = min(size, (size_t)(BUFFER_SIZE - *offset));

    if (bytes_to_write == 0) {
        return 0;
    }

    if (copy_from_user(device_buffer + *offset, user_buffer, bytes_to_write)) {
        return -EFAULT;
    }

    *offset += bytes_to_write;
    return bytes_to_write;
}

static int arkhe_bus_mmap(struct file *file, struct vm_area_struct *vma) {
    unsigned long size = vma->vm_end - vma->vm_start;

    pr_info("Arkhe Bus: mmap invoked\n");

    if (size > BUFFER_SIZE) {
        return -EINVAL;
    }

    if (remap_vmalloc_range(vma, device_buffer, 0)) {
        return -EAGAIN;
    }

    return 0;
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = arkhe_bus_open,
    .release = arkhe_bus_release,
    .read = arkhe_bus_read,
    .write = arkhe_bus_write,
    .mmap = arkhe_bus_mmap,
};

static int __init arkhe_bus_init(void) {
    dev_t dev;

    pr_info("Arkhe Bus: Initializing the Arkhe Bus V3 kernel module\n");

    device_buffer = vmalloc_user(BUFFER_SIZE);
    if (!device_buffer) {
        pr_alert("Arkhe Bus: Failed to allocate device buffer\n");
        return -ENOMEM;
    }

    // Initialize buffer to zero
    memset(device_buffer, 0, BUFFER_SIZE);

    if (alloc_chrdev_region(&dev, 0, 1, DEVICE_NAME) < 0) {
        pr_alert("Arkhe Bus: Failed to allocate a major number\n");
        vfree(device_buffer);
        return -EBUSY;
    }
    major_number = MAJOR(dev);

    arkhe_bus_class = class_create(CLASS_NAME);
    if (IS_ERR(arkhe_bus_class)) {
        unregister_chrdev_region(dev, 1);
        vfree(device_buffer);
        pr_alert("Arkhe Bus: Failed to register device class\n");
        return PTR_ERR(arkhe_bus_class);
    }

    cdev_init(&arkhe_bus_cdev, &fops);
    if (cdev_add(&arkhe_bus_cdev, dev, 1) < 0) {
        class_destroy(arkhe_bus_class);
        unregister_chrdev_region(dev, 1);
        vfree(device_buffer);
        pr_alert("Arkhe Bus: Failed to add cdev\n");
        return -EBUSY;
    }

    arkhe_bus_device = device_create(arkhe_bus_class, NULL, dev, NULL, DEVICE_NAME);
    if (IS_ERR(arkhe_bus_device)) {
        cdev_del(&arkhe_bus_cdev);
        class_destroy(arkhe_bus_class);
        unregister_chrdev_region(dev, 1);
        vfree(device_buffer);
        pr_alert("Arkhe Bus: Failed to create the device\n");
        return PTR_ERR(arkhe_bus_device);
    }

    pr_info("Arkhe Bus: Arkhe Bus Driver V3 installed successfully\n");
    return 0;
}

static void __exit arkhe_bus_exit(void) {
    dev_t dev = MKDEV(major_number, 0);

    vfree(device_buffer);
    cdev_del(&arkhe_bus_cdev);
    device_destroy(arkhe_bus_class, dev);
    class_destroy(arkhe_bus_class);
    unregister_chrdev_region(dev, 1);
    pr_info("Arkhe Bus: Arkhe Bus Driver V3 uninstalled successfully\n");
}

module_init(arkhe_bus_init);
module_exit(arkhe_bus_exit);
