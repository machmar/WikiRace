#!/bin/sh
# Launch WikiRace, installing Python first if this machine doesn't have it.

set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE" || exit 1

usable() {
    command -v "$1" >/dev/null 2>&1 || return 1
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null || return 1
    command -v "$1"
}

find_python() {
    for c in python3 python python3.13 python3.12 python3.11 python3.10 python3.9; do
        if p=$(usable "$c"); then
            printf '%s\n' "$p"
            return 0
        fi
    done
    return 1
}

if ! PY=$(find_python); then
    printf '\n  Python 3.8+ is needed and I could not find it - running setup.\n\n'
    sh "$HERE/setup.sh" || exit 1
    if ! PY=$(find_python); then
        printf '\n  Still no usable Python. Run ./setup.sh and read what it reports.\n\n'
        exit 1
    fi
fi

exec "$PY" "$HERE/wikirace.py" "$@"
