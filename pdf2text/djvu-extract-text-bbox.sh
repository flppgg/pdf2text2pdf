#!/bin/bash
installdir="$1"
file="$2"
pages=`djvused -e n "$file"`
if [ $pages -gt 0 ]; then
    echo $pages
    djvused -e 'print-txt' "$file" | perl "$installdir"/normalize_djvu_txt.pl
else
    echo "Error: Cannot determine number of pages in DJVU file '$file'" >&2
    exit 1
fi
