#!/bin/bash

output_file="ProjectSummary.md"

printf '%s\n' "# Project Summary" >"$output_file"

git ls-files | sort -u | while IFS= read -r file; do
    # Exclude generated protobuf files, the output file itself, this script, tests, helper scripts, and minified assets.
    case "$file" in
        *.pb.go|ProjectSummary.md|summarize.sh|tests/*|generate_hints_categories.py|style.min.css|web/package-lock.json|api/src/api/slug_config.toml|web/src/lib/client/*|api/src/api/db/query.py|api/src/api/db/models.py|*config.ts*|*config.js*|*package.json) continue ;;
    esac

    case "$file" in
        *.cpp|*.h|*.hpp|*.c|*.cs|*.py|*.js|*.ts|*.java|*.go|*.rs|*.nim|*.sh|*.ps1|*.gd|*.html|*.css|*.yaml|*.json|*.toml|*.svelte) ;;
        *) continue ;;
    esac

    case "$file" in
        *.cpp|*.h|*.hpp) lang="cpp" ;;
        *.c) lang="c" ;;
        *.cs) lang="csharp" ;;
        *.py) lang="python" ;;
        *.js) lang="javascript" ;;
        *.ts) lang="typescript" ;;
        *.java) lang="java" ;;
        *.go) lang="go" ;;
        *.rs) lang="rust" ;;
        *.nim) lang="nim" ;;
        *.sh) lang="bash" ;;
        *.ps1) lang="powershell" ;;
        *.gd) lang="gdscript" ;;
        *.html) lang="html" ;;
        *.css) lang="css" ;;
        *) lang="" ;;
    esac

    printf '\n## %s\n' "$file" >>"$output_file"
    printf '```%s\n' "$lang" >>"$output_file"
    case "$file" in
        incowhatsit/cards.py)
            # Truncate card definitions: show header + first 2 cards, then ...etc, then last card + closing
            head -n 13 "$file" >>"$output_file"
            printf '    # ... etc\n' >>"$output_file"
            tail -n 2 "$file" >>"$output_file"
            ;;
        *)
            while IFS= read -r line; do
                printf '%s\n' "$line"
            done <"$file" >>"$output_file"
            ;;
    esac
    printf '```\n' >>"$output_file"
done
