#include <stdint.h>

struct gpio_req {
    int pin;
    int val;
};

struct timespec_arm {
    long tv_sec;
    long tv_nsec;
};

// system call Linux ARM EABI
static inline long sys_call3(long num, long a0, long a1, long a2) {
    register long r7 __asm__("r7") = num;
    register long r0 __asm__("r0") = a0;
    register long r1 __asm__("r1") = a1;
    register long r2 __asm__("r2") = a2;
    __asm__ volatile ("svc #0" : "+r"(r0) : "r"(r7), "r"(r1), "r"(r2) : "memory");
    return r0;
}

static int sys_open(const char *path, int flags) { return (int)sys_call3(5, (long)path, flags, 0); }
static int sys_close(int fd) { return (int)sys_call3(6, fd, 0, 0); }
static long sys_write(int fd, const void *buf, long len) { return sys_call3(4, fd, (long)buf, len); }
static int sys_ioctl(int fd, unsigned long req, void *arg) { return (int)sys_call3(54, fd, (long)req, (long)arg); }

static void sys_usleep(unsigned long us) {
    struct timespec_arm ts = { 0, (long)(us * 1000UL) };
    sys_call3(162, (long)&ts, 0, 0);
}

static void print_str(const char *s) {
    long len = 0;
    while (s[len]) len++;
    sys_write(1, s, len);
}

static int str_eq(const char *a, const char *b) {
    while (*a && *b) {
        if (*a++ != *b++) return 0;
    }
    return *a == *b;
}

static int parse_int(const char *s) {
    int v = 0;
    while (*s >= '0' && *s <= '9') {
        v = v * 10 + (*s++ - '0');
    }
    return v;
}

// .rodata (0xae338 oraz 0xae344)
static const uint8_t seq_dir0[9] = { 0x09, 0x08, 0x0c, 0x04, 0x06, 0x02, 0x03, 0x01, 0x00 }; // left / down
static const uint8_t seq_dir1[9] = { 0x01, 0x03, 0x02, 0x06, 0x04, 0x0c, 0x08, 0x09, 0x00 }; // right / up

static int gpio_fd = -1;

static void set_bank0_pin(int pin, int val) {
    struct gpio_req req = { pin, val };
    sys_ioctl(gpio_fd, 5, &req);
}

static int read_limit_switch(int pin) {
    uint32_t mask = 0;
    sys_ioctl(gpio_fd, 4, &mask);
    return ((mask >> pin) & 1) == 0;
}

static void set_motor_phase(int axis, int dir, int phase, unsigned long delay_us) {
    const int pins_pan[4]  = { 14, 15, 16, 17 };
    const int pins_tilt[4] = { 21, 20, 19, 18 };
    const int *pins = (axis == 1) ? pins_tilt : pins_pan;
    uint8_t bits = (dir == 0) ? seq_dir0[phase] : seq_dir1[phase];

    uint32_t clear_mask = 0, set_mask = 0;
    for (int i = 0; i < 4; i++) {
        clear_mask |= (1U << pins[i]);
        if ((bits >> i) & 1) {
            set_mask |= (1U << pins[i]);
        }
    }

    uint32_t port_val = 0;
    sys_ioctl(gpio_fd, 8, &port_val);
    port_val = (port_val & ~clear_mask) | set_mask;
    sys_ioctl(gpio_fd, 7, &port_val);

    if (delay_us > 0) {
        sys_usleep(delay_us);
    }
}

static void step_axis(int axis, int dir, int steps, unsigned long delay_us) {
    for (int s = 0; s < steps; s++) {
        if (axis == 0 && dir == 0 && read_limit_switch(28)) { print_str("Limit: LEFT\n"); break; }
        if (axis == 0 && dir == 1 && read_limit_switch(27)) { print_str("Limit: RIGHT\n"); break; }
        if (axis == 1 && dir == 1 && read_limit_switch(30)) { print_str("Limit: UP\n"); break; }
        if (axis == 1 && dir == 0 && read_limit_switch(20)) { print_str("Limit: DOWN\n"); break; }

        for (int p = 0; p < 8; p++) {
            set_motor_phase(axis, dir, p, delay_us);
        }
    }
    set_motor_phase(axis, 0, 8, 0);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        print_str("usage:\n  ./ptz_test pan <0|1> <kroki>\n  ./ptz_test tilt <0|1> <kroki>\n  ./ptz_test ircut <0|1>\n  ./ptz_test irled <0|1>\n");
        return 1;
    }

    gpio_fd = sys_open("/dev/gpio0", 2); // O_RDWR = 2
    if (gpio_fd < 0) {
        print_str("Can't open /dev/gpio0\n");
        return 1;
    }

    if (str_eq(argv[1], "pan") && argc >= 4) {
        step_axis(0, parse_int(argv[2]), parse_int(argv[3]), 1800);
    } else if (str_eq(argv[1], "tilt") && argc >= 4) {
        step_axis(1, parse_int(argv[2]), parse_int(argv[3]), 2500);
    } else if (str_eq(argv[1], "ircut") && argc >= 3) {
        set_bank0_pin(3, parse_int(argv[2]));
    } else if (str_eq(argv[1], "irled") && argc >= 3) {
        set_bank0_pin(0, parse_int(argv[2]));
    } else {
        print_str("Unknown command\n");
    }

    sys_close(gpio_fd);
    return 0;
}

__attribute__((naked)) void _start(void) {
    __asm__ volatile (
        "ldr r0, [sp]\n"
        "add r1, sp, #4\n"
        "bic sp, sp, #7\n"
        "bl main\n"
        "mov r7, #1\n"
        "svc #0\n"
    );
}