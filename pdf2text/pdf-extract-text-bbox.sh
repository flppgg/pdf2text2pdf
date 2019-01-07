#!/bin/bash

ulimit="ulimit -t 360"
p2t="pdftotext -layout -enc UTF-8 -bbox"

installdir="$1"
file="$2"

# Determine the number of pages.
pages=`pdfinfo "$file" | LC_ALL=C grep -a '^Pages:     ' | sed -e 's/^.*[^0-9]\([0-9][0-9]*\)$/\1/g;'`

if [ $pages -gt 0 ]; then

		echo "$pages"
		($ulimit; $p2t "$file" - | perl "$installdir"/normalize_pdf_html.pl)

else
	echo "Error: Cannot determine number of pages in PDF file '$file'" >&2
	exit 1
fi


