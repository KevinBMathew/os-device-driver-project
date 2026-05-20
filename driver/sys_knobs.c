//since i am using a modern kernel for this assignment, i needed to use module_init() and module_exit() instead of the 
// old function names init_module and cleanup_module.

#include <linux/module.h>
#include <linux/string.h>
#include <linux/fs.h>
#include <linux/uaccess.h>

// module data
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("SysKnobs – Potentiometer Based Volume & Brightness Knobs");
MODULE_AUTHOR("Kevin Benny Mathew");

#define DEVICE_NAME  "sys_knobs"
#define BUF_SIZE     64          

static int  major_number;
static char knobs_data[BUF_SIZE] = "V:0 B:0";
static int  data_len = 7;

// functions prototypes
static int     dev_open (struct inode *, struct file *);
static int     dev_rls  (struct inode *, struct file *);
static ssize_t dev_read (struct file *, char __user *, size_t, loff_t *);
static ssize_t dev_write(struct file *, const char __user *, size_t, loff_t *);

// mapping table
static struct file_operations fops = {
    .read    = dev_read,
    .write   = dev_write,
    .open    = dev_open,
    .release = dev_rls,
};

// dev_open is called when the device file is opened. It simply logs a message and returns 0 to indicate success.
static int dev_open(struct inode *inod, struct file *fil)
{
    printk(KERN_INFO "sys_knobs: Device opened\n");
    return 0;
}

// dev_read is called when the device file is read. It copies the stored data to the user buffer and returns the number of bytes copied.
static ssize_t dev_read(struct file *filp, char __user *buff,
                        size_t len, loff_t *off)
{
    ssize_t available;
    ssize_t to_copy;
    unsigned long not_copied;

    if (*off >= data_len)
        return 0;
 
    available = data_len - (int)*off;
    to_copy   = min((ssize_t)len, available);

    not_copied = copy_to_user(buff, knobs_data + *off, to_copy);

    *off += (to_copy - not_copied);
    return (to_copy - not_copied);
}

//dev write returns the number of bytes successfully written, or a negative error code on failure. 
//The copy_from_user function returns the number of bytes that were not copied, so we need to subtract 
//that from the intended length to get the actual number of bytes written.
static ssize_t dev_write(struct file *filp, const char __user *buff,
                         size_t len, loff_t *off)
{
    unsigned long not_copied;  

    if (len >= BUF_SIZE)            //clamp to max buffer size (leave space for null terminator)
        len = BUF_SIZE - 1;

    memset(knobs_data, 0, BUF_SIZE);

    not_copied = copy_from_user(knobs_data, buff, len);

    data_len = len - not_copied;
    knobs_data[data_len] = '\0';    //ensure null-terminated string

    printk(KERN_INFO "sys_knobs: Stored -> \"%s\"\n", knobs_data);
    return data_len;
}

//dev_rls is called when the device file is closed. It simply logs a message and returns 0 to indicate success.
static int dev_rls(struct inode *inod, struct file *fil)
{
    printk(KERN_INFO "sys_knobs: Device closed\n");
    return 0;
}

// sys_knobs_init is the initialization function that runs when the module is loaded. 
// It registers the character device and prints instructions for creating the device file. 
// If registration fails, it logs an error and returns the failure code.
static int __init sys_knobs_init(void)
{
    major_number = register_chrdev(0, DEVICE_NAME, &fops);

    if (major_number < 0) {
        printk(KERN_ALERT "sys_knobs: Device registration failed (%d)\n",
               major_number);
        return major_number;
    }

    printk(KERN_INFO "sys_knobs: Registered – major number = %d\n",
           major_number);
    printk(KERN_INFO "sys_knobs: Now run:\n");
    printk(KERN_INFO "  sudo mknod /dev/sys_knobs c %d 0\n", major_number);
    printk(KERN_INFO "  sudo chmod a+rw /dev/sys_knobs\n");
    return 0;
}

static void __exit sys_knobs_exit(void)
{
    unregister_chrdev(major_number, DEVICE_NAME);
    printk(KERN_INFO "sys_knobs: Unregistered. Goodbye.\n");
}

module_init(sys_knobs_init);
module_exit(sys_knobs_exit);
