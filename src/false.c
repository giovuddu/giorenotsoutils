#include <string.h>
#include <stdio.h>
#include "version.h"

#define PROG "false"

void usage(char * prog) {
    printf(
        "Usage: %s [ignored command line arguments]\n"
        "  or:  %s OPTION\n"
        "Exit with a status code indicating failure.\n"
        "\n"
        "      --help        display this help and exit\n"
        "      --version     output version information and exit\n"
        "\n"
        "Your shell may have its own version of false, which usually supersedes\n"
        "the version described here.  Please refer to your shell's documentation\n"
        "for details about the options it supports.\n"
        "\n"
        "GIOVUDDU giorenotsoutils online help: <https://www.giovuddu.org/software/giorenotsoutils/>\n"
        "Full documentation <https://www.giovuddu.org/software/giorenotsoutils/true>\n"
        "or available locally... wait... no'\n", prog, prog);
}

int main(int argc, char *argv[]) {
    if (argc == 2) {
        if (strcmp(argv[1], "--version") == 0) {
            version(PROG);
            return 1;
        }
        if (strcmp(argv[1], "--help") == 0) {
            usage(argv[0]);
            return 1;
        }
    }
    return 1;
}

