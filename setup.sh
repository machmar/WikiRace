#!/bin/sh
# WikiRace setup for Linux and macOS.
#
# The game has no third-party dependencies - it's written against the Python
# standard library only, so there is nothing to pip install. This just makes
# sure a new enough Python is present.

set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Installing system packages is never silent by default. Pass -y (or set
# WIKIRACE_YES=yes) to allow it unattended, e.g. on a headless box.
ASSUME_YES=${WIKIRACE_YES:-no}
for arg in "$@"; do
    case $arg in
        -y|--yes) ASSUME_YES=yes ;;
    esac
done

if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
    CYAN=$(tput setaf 6); RESET=$(tput sgr0)
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; RESET=''
fi

say()   { printf '  %s\n' "$*"; }
ok()    { printf '  %s%s%s\n' "$GREEN" "$*" "$RESET"; }
warn()  { printf '  %s%s%s\n' "$YELLOW" "$*" "$RESET"; }
bad()   { printf '  %s%s%s\n' "$RED" "$*" "$RESET"; }

# Prints the interpreter path if it's Python 3.8+, otherwise nothing.
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

# Work out how this machine installs software, and what it calls Python.
detect_installer() {
    if [ "$(uname -s)" = "Darwin" ]; then
        if command -v brew >/dev/null 2>&1; then
            PKG_DESC="Homebrew"; PKG_CMD="brew install python"; PKG_SUDO=no
            return 0
        fi
        PKG_DESC=""; return 1
    fi
    if command -v apt-get >/dev/null 2>&1; then
        PKG_DESC="apt"; PKG_CMD="apt-get update && apt-get install -y python3"; PKG_SUDO=yes
    elif command -v dnf >/dev/null 2>&1; then
        PKG_DESC="dnf"; PKG_CMD="dnf install -y python3"; PKG_SUDO=yes
    elif command -v pacman >/dev/null 2>&1; then
        PKG_DESC="pacman"; PKG_CMD="pacman -S --needed --noconfirm python"; PKG_SUDO=yes
    elif command -v zypper >/dev/null 2>&1; then
        PKG_DESC="zypper"; PKG_CMD="zypper install -y python3"; PKG_SUDO=yes
    elif command -v apk >/dev/null 2>&1; then
        PKG_DESC="apk"; PKG_CMD="apk add python3"; PKG_SUDO=yes
    else
        PKG_DESC=""; return 1
    fi
    return 0
}

printf '\n  %sWikiRace setup%s\n' "$CYAN" "$RESET"
printf '  --------------\n'
say "The game needs no extra packages - it uses only Python's standard"
say "library. This just makes sure Python itself is installed."
printf '\n'

if PY=$(find_python); then
    ok "Found $("$PY" -V 2>&1) at $PY"
else
    say "No Python 3.8 or newer found."
    if ! detect_installer; then
        bad "I don't recognise this system's package manager."
        printf '\n'
        say "Install Python 3 with whatever this distribution uses, then re-run."
        printf '\n'
        exit 1
    fi

    if [ "$PKG_SUDO" = yes ] && [ "$(id -u)" -ne 0 ]; then
        RUN="sudo sh -c '$PKG_CMD'"
    else
        RUN="sh -c '$PKG_CMD'"
    fi

    printf '\n'
    say "This will install Python using $PKG_DESC:"
    printf '\n      %s\n\n' "$RUN"
    if [ "$ASSUME_YES" = yes ]; then
        reply=y
        say "Proceeding without asking (-y given)."
    elif [ -t 0 ]; then
        printf '  Go ahead? [y/N] '
        read -r reply || reply=n
    else
        reply=n
        warn "No terminal to ask on, so nothing will be installed."
        say "Re-run this directly, or pass -y to allow it unattended."
    fi
    case "$reply" in
        [Yy]*) ;;
        *) printf '\n'; warn "Skipped. Install Python 3 yourself, then re-run this."; printf '\n'; exit 1 ;;
    esac

    printf '\n'
    if [ "$PKG_SUDO" = yes ] && [ "$(id -u)" -ne 0 ]; then
        sudo sh -c "$PKG_CMD" || true
    else
        sh -c "$PKG_CMD" || true
    fi
    printf '\n'

    if ! PY=$(find_python); then
        bad "Python still isn't available after that."
        printf '\n'
        say "Install it by hand, then run this again."
        printf '\n'
        exit 1
    fi
    ok "Installed $("$PY" -V 2>&1)"
fi

# Prove this interpreter can really run the game, not just report a version -
# some slim distro images ship a Python without the full standard library.
if [ -f "$HERE/wikirace.py" ]; then
    if ! "$PY" -c '
import sys, py_compile
for m in ("socket","json","threading","hashlib","uuid","webbrowser","struct","http.server"):
    __import__(m)
py_compile.compile(sys.argv[1], doraise=True)
' "$HERE/wikirace.py"; then
        printf '\n'
        bad "That Python could not run the game (details above)."
        say "On Debian/Ubuntu a minimal image may need: sudo apt-get install python3-minimal"
        printf '\n'
        exit 1
    fi
fi

chmod +x "$HERE/play.sh" 2>/dev/null || true

printf '\n'
ok "All set - the game compiles and is ready to run."
printf '\n'
say "Start playing with:   ./play.sh"
say "Everyone on the same network runs it, then one of you starts a race."
printf '\n'
exit 0
