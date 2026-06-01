#!/bin/bash
# Generate PDFs from Markdown files with Mermaid diagrams pre-rendered as SVG
# Requires: md-to-pdf, @mermaid-js/mermaid-cli (mmdc)
# Usage: ./generate-pdfs.sh

set -e

OUTPUT_DIR="Business Analysis/PDF"
TEMP_DIR="Business Analysis/.tmp_pdf"
mkdir -p "$OUTPUT_DIR" "$TEMP_DIR"

FRONT_MATTER='---
pdf_options:
  format: A4
  margin: 20mm
  printBackground: true
css: |-
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
  th { background-color: #f5f5f5; }
  code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
  pre { background: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; }
  img { max-width: 100%; }
  svg { max-width: 100%; height: auto; }
---

'

for md_file in "Business Analysis"/*.md; do
  filename=$(basename "$md_file" .md)
  echo "Processing: $filename"
  
  tmp_md="$TEMP_DIR/$filename.md"
  
  # Start with front-matter
  printf '%s' "$FRONT_MATTER" > "$tmp_md"
  
  # Process the file: extract mermaid blocks, render them as SVG, inline them
  in_mermaid=false
  mermaid_content=""
  diagram_count=0
  
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == '```mermaid' ]]; then
      in_mermaid=true
      mermaid_content=""
      continue
    fi
    
    if $in_mermaid; then
      if [[ "$line" == '```' ]]; then
        in_mermaid=false
        diagram_count=$((diagram_count + 1))
        
        # Write mermaid content to temp file and render as SVG
        mmd_file="$TEMP_DIR/${filename}_diagram_${diagram_count}.mmd"
        svg_file="$TEMP_DIR/${filename}_diagram_${diagram_count}.svg"
        
        printf '%s\n' "$mermaid_content" > "$mmd_file"
        
        if mmdc -i "$mmd_file" -o "$svg_file" -b transparent 2>/dev/null; then
          # Inline the SVG content
          echo "" >> "$tmp_md"
          cat "$svg_file" >> "$tmp_md"
          echo "" >> "$tmp_md"
        else
          # Fallback: show as code block if rendering fails
          echo '```' >> "$tmp_md"
          printf '%s\n' "$mermaid_content" >> "$tmp_md"
          echo '```' >> "$tmp_md"
          echo "  ⚠ Diagram $diagram_count failed to render"
        fi
      else
        mermaid_content="${mermaid_content}${line}
"
      fi
    else
      printf '%s\n' "$line" >> "$tmp_md"
    fi
  done < "$md_file"
  
  # Generate PDF
  md-to-pdf "$tmp_md" 2>&1
  
  # Move PDF to output dir
  if [[ -f "$TEMP_DIR/$filename.pdf" ]]; then
    mv "$TEMP_DIR/$filename.pdf" "$OUTPUT_DIR/$filename.pdf"
  fi
done

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Done! PDFs generated in: $OUTPUT_DIR/"
ls -la "$OUTPUT_DIR"/*.pdf 2>/dev/null
