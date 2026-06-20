#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>

#include "version.h"
#include "help.h"

#define PROG "yes"

static struct option const long_opts[] = {
    {"help",    no_argument, NULL, 'h'},
    {"version", no_argument, NULL, 'v'},
    {NULL, 0, NULL, 0}
};

void usage(char * prog) {
    printf(
        "Usage: %s [STRING]...\n"
        "  or:  %s OPTION\n"
        "Repeatedly output a line with all specified STRING(s), or 'y'.\n"
        "\n"
        "      --help        display this help and exit\n"
        "      --version     output version information and exit\n"
        HELP_FOOTER
        , prog, prog);
};

void concat_args(char **args, size_t *args_lengths, int len, char *buf) {
    for ( int i = 0; i < len; i++ ) {
        memcpy(buf, args[i], args_lengths[i]);
        buf += args_lengths[i];
        *buf++ = ' ';
    }
    *(buf - 1) = '\0';
};

void *xmalloc(size_t size) {
    void *p = malloc(size);
    if (!p) {
        fprintf(stderr, "%s: oom", PROG);
        exit(EXIT_FAILURE);
    }
    return p;
}

int main(int argc, char *argv[]) {
    char *str = "y";

    int c;
    while ((c = getopt_long(argc, argv, "", long_opts, NULL)) != -1) {
        switch (c) {
            case 'v':
                version(PROG);
                return EXIT_SUCCESS;
            case 'h':
                usage(argv[0]);
                return EXIT_SUCCESS;
            default:
                fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
                return EXIT_FAILURE;
        }
    }

    int str_args_len = argc - optind;
    if (str_args_len > 0) {
        char **str_args = argv + optind;
        size_t buf_len = 0;

        size_t *args_lengths = xmalloc((str_args_len) * sizeof(size_t));

        for (int i = 0; i < str_args_len; i++) {
            args_lengths[i] = strlen(str_args[i]);
            buf_len += args_lengths[i];
        }
        buf_len += str_args_len;

        char *buf = xmalloc(buf_len);
        concat_args(str_args, args_lengths, str_args_len, buf);

        str = buf;
        free(args_lengths);
    }

    setvbuf(stdout, NULL, _IOFBF, 64 * 1024); 
    while (1) {
        puts(str);
    }
}
