#!/usr/bin/env bash

set -euo pipefail

green='\033[0;32m'
yellow='\033[1;33m'
red='\033[0;31m'
nc='\033[0m'

ok() { printf "${green}OK${nc} %s\n" "$1"; }
warn() { printf "${yellow}WARN${nc} %s\n" "$1"; }
fail() { printf "${red}FAIL${nc} %s\n" "$1"; }

if [[ ! -f "AGENTS.md" ]]; then
  fail "Run this script from the repository root"
  exit 1
fi

ok "Working directory: $(pwd)"

for required in AGENTS.md ARCHITECTURE.md feature_list.json progress.md docs/INTERFACES.md docs/DATA_SPEC.md docs/DECISIONS.md; do
  if [[ -f "$required" ]]; then
    ok "Found $required"
  else
    fail "Missing required file: $required"
    exit 1
  fi
done

setup_python_module() {
  local mod="$1"
  if [[ ! -d "$mod" ]]; then
    warn "Module directory missing: $mod"
    return
  fi

  if [[ -f "$mod/requirements.txt" ]]; then
    ok "$mod has requirements.txt"
  fi

  if [[ -f "$mod/.env.example" && ! -f "$mod/.env" ]]; then
    cp "$mod/.env.example" "$mod/.env"
    warn "$mod/.env created from .env.example"
  fi
}

setup_node_module() {
  local mod="$1"
  if [[ ! -d "$mod" ]]; then
    warn "Module directory missing: $mod"
    return
  fi

  if [[ -f "$mod/package.json" ]]; then
    ok "$mod has package.json"
  fi

  if [[ -f "$mod/.env.example" && ! -f "$mod/.env.local" ]]; then
    cp "$mod/.env.example" "$mod/.env.local"
    warn "$mod/.env.local created from .env.example"
  fi
}

setup_node_module frontend
setup_python_module chatbot
setup_python_module lora
setup_python_module rag

printf "\nNext steps:\n"
printf "  1. Read the target module's AGENTS.md\n"
printf "  2. Open the module feature_list.json\n"
printf "  3. Implement one feature at a time\n"

