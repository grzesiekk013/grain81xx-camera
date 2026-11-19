#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

#define SNAP_OUT_PATH "/tmp/snap_latest.bin"

static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static FILE *g_tracked_fp = NULL;
static FILE *g_mirror_fp = NULL;

static FILE *(*real_fopen)(const char *pathname, const char *mode) = NULL;
static size_t (*real_fwrite)(const void *ptr, size_t size, size_t nmemb, FILE *stream) = NULL;
static int (*real_fclose)(FILE *stream) = NULL;

static void init_syms(void) {
    if (!real_fopen)  real_fopen  = dlsym(RTLD_NEXT, "fopen");
    if (!real_fwrite) real_fwrite = dlsym(RTLD_NEXT, "fwrite");
    if (!real_fclose) real_fclose = dlsym(RTLD_NEXT, "fclose");
}

FILE *fopen(const char *pathname, const char *mode) {
    init_syms();
    FILE *fp = real_fopen(pathname, mode);
    if (!fp || !pathname) return fp;

    if (strstr(pathname, "alarm") && strstr(pathname, ".jpg")) {
        pthread_mutex_lock(&g_lock);
        if (g_mirror_fp) {
            real_fclose(g_mirror_fp);
            g_mirror_fp = NULL;
        }
        g_tracked_fp = fp;
        g_mirror_fp = real_fopen(SNAP_OUT_PATH, "wb");
        if (g_mirror_fp) {
            fprintf(stderr, "[hook] capturing %s -> %s\n", pathname, SNAP_OUT_PATH);
        }
        pthread_mutex_unlock(&g_lock);
    }
    return fp;
}

size_t fwrite(const void *ptr, size_t size, size_t nmemb, FILE *stream) {
    init_syms();
    size_t ret = real_fwrite(ptr, size, nmemb, stream);

    pthread_mutex_lock(&g_lock);
    if (stream && stream == g_tracked_fp && g_mirror_fp && ret > 0) {
        real_fwrite(ptr, size, ret, g_mirror_fp);
        fflush(g_mirror_fp);
    }
    pthread_mutex_unlock(&g_lock);

    return ret;
}

int fclose(FILE *stream) {
    init_syms();
    pthread_mutex_lock(&g_lock);
    if (stream && stream == g_tracked_fp) {
        g_tracked_fp = NULL;
        if (g_mirror_fp) {
            real_fclose(g_mirror_fp);
            g_mirror_fp = NULL;
            fprintf(stderr, "[hook] saved snapshot to %s\n", SNAP_OUT_PATH);
        }
    }
    pthread_mutex_unlock(&g_lock);

    return real_fclose(stream);
}