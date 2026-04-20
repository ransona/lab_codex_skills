#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"

mkdir -p "$skills_dir"

found=0
for skill_path in "$repo_dir"/*; do
    [ -d "$skill_path" ] || continue
    [ -f "$skill_path/SKILL.md" ] || continue

    found=1
    skill_name="$(basename "$skill_path")"
    dest="$skills_dir/$skill_name"

    if [ -e "$dest" ]; then
        while true; do
            read -r -p "Skill '$skill_name' already exists. Overwrite? [y/N] " answer
            case "$answer" in
                [yY]|[yY][eE][sS])
                    rm -rf "$dest"
                    cp -a "$skill_path" "$dest"
                    echo "Updated $dest"
                    break
                    ;;
                ""|[nN]|[nN][oO])
                    echo "Skipped $skill_name"
                    break
                    ;;
                *)
                    echo "Please answer y or n."
                    ;;
            esac
        done
    else
        cp -a "$skill_path" "$dest"
        echo "Installed $dest"
    fi
done

if [ "$found" -eq 0 ]; then
    echo "No skill folders found in $repo_dir"
fi

