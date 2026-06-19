#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include "version.h"
#include "help.h"

#define PROG "yes"

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

int main(int argc, char *argv[]) {
    char *str = "y";

    if (argc > 1) {
        // tbd unhandled option stuff. oof
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "--version") == 0) {
                version(PROG);
                return 0;
            }
            if (strcmp(argv[i], "--help") == 0) {
                usage(argv[0]);
                return 0;
            }
        }

        char **str_args = argv + 1;
        size_t buf_len = 0;
        // heap to prevent stack overflow in case of a LOT of arguments
        size_t *args_lengths = malloc((argc-1) * sizeof(size_t));

        for (int i = 0; i < argc-1; i++) {
            args_lengths[i] = strlen(str_args[i]);
            buf_len += args_lengths[i];
        }
        buf_len += argc-1;

        char *buf = malloc(buf_len);
        concat_args(str_args, args_lengths, argc-1, buf);

        str = buf;
    }

    while (1) {
        printf("%s\n", str);
    }
}
