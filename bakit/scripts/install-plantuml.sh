#!/usr/bin/env bash

set -euo pipefail

if command -v plantuml >/dev/null 2>&1; then
  printf 'PlantUML already available at %s\n' "$(command -v plantuml)"
  exit 0
fi

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi
  printf 'Need elevated privileges to run: %s\n' "$*" >&2
  exit 1
}

install_with_brew() {
  brew install plantuml
}

install_with_apt() {
  run_root apt-get update
  run_root apt-get install -y default-jre-headless graphviz plantuml
}

install_with_dnf() {
  run_root dnf install -y java-17-openjdk-headless graphviz plantuml
}

install_with_yum() {
  run_root yum install -y java-17-openjdk-headless graphviz plantuml
}

install_with_pacman() {
  run_root pacman -Sy --noconfirm jre-headless graphviz plantuml
}

main() {
  if command -v brew >/dev/null 2>&1; then
    install_with_brew
  elif command -v apt-get >/dev/null 2>&1; then
    install_with_apt
  elif command -v dnf >/dev/null 2>&1; then
    install_with_dnf
  elif command -v yum >/dev/null 2>&1; then
    install_with_yum
  elif command -v pacman >/dev/null 2>&1; then
    install_with_pacman
  else
    printf 'No supported package manager found for automatic PlantUML installation.\n' >&2
    printf 'Install PlantUML locally, then retry.\n' >&2
    exit 1
  fi

  if ! command -v plantuml >/dev/null 2>&1; then
    printf 'PlantUML installation command completed, but `plantuml` is still unavailable on PATH.\n' >&2
    exit 1
  fi

  printf 'PlantUML installed at %s\n' "$(command -v plantuml)"
}

main "$@"
