#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf "===================================\n"
printf "EXTERNAL RESOURCES AUDIT\n"
printf "===================================\n\n"

printf "Searching for external scripts...\n"
rg -n 'src="https?://' "$ROOT_DIR/app" "$ROOT_DIR/components" "$ROOT_DIR/public" || echo "None found in src="

printf "\nSearching for external stylesheets...\n"
rg -n 'href="https?://' "$ROOT_DIR/app" "$ROOT_DIR/components" "$ROOT_DIR/public" || echo "None found in href="

printf "\nSearching for CDN imports...\n"
rg -n 'cdn\.jsdelivr|unpkg\.com|cdnjs\.cloudflare|googletagmanager|fonts\.googleapis|accounts\.google\.com' "$ROOT_DIR/app" "$ROOT_DIR/components" "$ROOT_DIR/public" || echo "No CDN imports found"

printf "\n===================================\n"
printf "AUDIT COMPLETE\n"
printf "===================================\n"
