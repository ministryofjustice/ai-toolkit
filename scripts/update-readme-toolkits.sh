#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
README_PATH="$ROOT_DIR/README.md"
TOOLKITS_DIR="$ROOT_DIR/toolkits"

START_MARKER="<!-- BEGIN GENERATED TOOLKITS -->"
END_MARKER="<!-- END GENERATED TOOLKITS -->"

if [[ ! -f "$README_PATH" ]]; then
  echo "README not found at $README_PATH" >&2
  exit 1
fi

if [[ ! -d "$TOOLKITS_DIR" ]]; then
  echo "Toolkits directory not found at $TOOLKITS_DIR" >&2
  exit 1
fi

title_case() {
  local value="$1"
  echo "$value" | tr '-' ' ' | awk '{
    for (i = 1; i <= NF; i++) {
      $i = toupper(substr($i, 1, 1)) substr($i, 2)
    }
    print
  }'
}

slug_words() {
  local value="$1"
  echo "$value" | tr '-' ' '
}

extract_description() {
  local manifest_path="$1"
  local description

  description="$(awk '/^description:[[:space:]]*/{
    sub(/^description:[[:space:]]*/, "", $0)
    print
    exit
  }' "$manifest_path")"

  if [[ "$description" == \"*\" && "$description" == *\" ]]; then
    description="${description:1:${#description}-2}"
  elif [[ "$description" == "'"*"'" ]]; then
    description="${description:1:${#description}-2}"
  fi

  echo "$description"
}

escape_pipes() {
  local value="$1"
  echo "${value//|/\\|}"
}

repeat_char() {
  local char="$1"
  local count="$2"

  printf "%*s" "$count" "" | tr ' ' "$char"
}

emit_markdown_table() {
  local rows_file="$1"
  local team_header="Team"
  local toolkit_header="Toolkit"
  local contents_header="Contents"
  local team_width="${#team_header}"
  local toolkit_width="${#toolkit_header}"
  local contents_width="${#contents_header}"
  local team
  local toolkit
  local contents

  while IFS=$'\t' read -r team toolkit contents; do
    [[ -z "$team" ]] && continue

    (( ${#team} > team_width )) && team_width="${#team}"
    (( ${#toolkit} > toolkit_width )) && toolkit_width="${#toolkit}"
    (( ${#contents} > contents_width )) && contents_width="${#contents}"
  done < "$rows_file"

  printf "| %-*s | %-*s | %-*s |\n" "$team_width" "$team_header" "$toolkit_width" "$toolkit_header" "$contents_width" "$contents_header"
  printf "| %s | %s | %s |\n" \
    "$(repeat_char '-' "$team_width")" \
    "$(repeat_char '-' "$toolkit_width")" \
    "$(repeat_char '-' "$contents_width")"

  while IFS=$'\t' read -r team toolkit contents; do
    [[ -z "$team" ]] && continue

    printf "| %-*s | %-*s | %-*s |\n" "$team_width" "$team" "$toolkit_width" "$toolkit" "$contents_width" "$contents"
  done < "$rows_file"
}

trim_trailing_whitespace() {
  local value="$1"

  while [[ "$value" == *[[:space:]] ]]; do
    value="${value%[[:space:]]}"
  done

  echo "$value"
}

normalize_description() {
  local family_name="$1"
  local family_display="$2"
  local toolkit_name="$3"
  local raw_description="$4"
  local description

  description="$(trim_trailing_whitespace "$raw_description")"

  if [[ -n "$description" ]]; then
    if [[ "${description,,}" == *" toolkit" ]]; then
      description="${description:0:${#description}-8}"
    fi

    if [[ "${description,,}" == *" instructions" ]]; then
      description="${description:0:${#description}-13}"
    elif [[ "${description,,}" == *" instruction" ]]; then
      description="${description:0:${#description}-12}"
    fi

    description="$(trim_trailing_whitespace "$description")"
  fi

  if [[ -z "$description" ]]; then
    if [[ "$toolkit_name" == "$family_name" ]]; then
      echo "$family_display instructions."
    else
      echo "$family_display $(slug_words "$toolkit_name") instructions."
    fi
    return
  fi

  if [[ "$toolkit_name" == "$family_name" ]]; then
    echo "$description instructions."
    return
  fi

  if [[ "$description" == "$family_display"* ]]; then
    echo "$description instructions."
    return
  fi

  echo "$family_display $(echo "$description" | tr '[:upper:]' '[:lower:]') instructions."
}

generate_rows_for_family() {
  local family_dir="$1"
  local family_name
  local family_display
  local manifests

  family_name="$(basename "$family_dir")"
  family_display="$(title_case "$family_name")"
  manifests="$(find "$family_dir" -mindepth 1 -maxdepth 2 -type f -name 'apm.yml' | sort || true)"

  if [[ -z "$manifests" ]]; then
    return 0
  fi

  while IFS= read -r manifest; do
    [[ -z "$manifest" ]] && continue

    local toolkit_dir
    local rel_toolkit_dir
    local toolkit_name
    local toolkit_display
    local description

    toolkit_dir="$(dirname "$manifest")"
    rel_toolkit_dir="${toolkit_dir#"$ROOT_DIR"/}"
    toolkit_name="$(basename "$toolkit_dir")"
    toolkit_display="$toolkit_name"

    description="$(normalize_description "$family_name" "$family_display" "$toolkit_name" "$(extract_description "$manifest")")"

    description="$(escape_pipes "$description")"

    printf "%s\t%s\t%s\n" "$family_display" "[$toolkit_display]($rel_toolkit_dir)" "$description"
  done <<< "$manifests"
}

GENERATED_CONTENT_FILE="$(mktemp)"
ROWS_FILE="$(mktemp)"
trap 'rm -f "$GENERATED_CONTENT_FILE" "$ROWS_FILE" "$UPDATED_README_FILE"' EXIT

if ! grep -q "^${START_MARKER}$" "$README_PATH" || ! grep -q "^${END_MARKER}$" "$README_PATH"; then
  echo "README is missing generated toolkit markers." >&2
  exit 1
fi

universal_dir="$TOOLKITS_DIR/universal"
if [[ -d "$universal_dir" ]]; then
  generate_rows_for_family "$universal_dir" >> "$ROWS_FILE"
fi

family_dirs="$(find "$TOOLKITS_DIR" -mindepth 1 -maxdepth 1 -type d ! -name 'universal' | sort)"
while IFS= read -r family_dir; do
  [[ -z "$family_dir" ]] && continue
  generate_rows_for_family "$family_dir" >> "$ROWS_FILE"
done <<< "$family_dirs"

{
  echo
  emit_markdown_table "$ROWS_FILE"
  echo
} > "$GENERATED_CONTENT_FILE"

UPDATED_README_FILE="$(mktemp)"
awk -v start="$START_MARKER" -v end="$END_MARKER" -v generated="$GENERATED_CONTENT_FILE" '
  $0 == start {
    print
    while ((getline line < generated) > 0) {
      print line
    }
    close(generated)
    skip = 1
    next
  }
  $0 == end {
    skip = 0
    print
    next
  }
  skip != 1 {
    print
  }
' "$README_PATH" > "$UPDATED_README_FILE"

mv "$UPDATED_README_FILE" "$README_PATH"

echo "Updated toolkit sections in README.md"
