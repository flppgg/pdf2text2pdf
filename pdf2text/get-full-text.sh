#!/bin/bash

# extract full text from ebooks, including full bounding box information
# needs to know the directory with scripts
# needs pdftotext, djvutxt, djvused, java, bzip2, md5sum, perl, pdfinfo
# needs tika-app-1.18.jar and will download it if not present

installdir="$1"
shift
storage="$1"
shift

if [ x"$1" == x ]; then
    echo "Usage: $0 install_dir storage_path file1 file2 file3 ..." >&2
    echo "Extract full text from files, write result files at storage_path/md5sum.ext.bz2"
    echo "install_dir should contain all scripts"
    exit 1
fi

function make_path {
    local f="$1" e="$2"
    md5=`md5sum < "$f" | cut -c 1-32`
# uncomment this to use subdirectories for storage; this is useful if storing many millions of files
#    d1=${md5:0:2}
#    d2=${md5:2:2}
#    dir="$storage/$d1/$d2"
    dir="$storage"
    test -d "$dir" || mkdir -p "$dir"
    dest="$dir/$md5.$e.ft.bz2"
    echo "For input file '$f', determined destination file name: '$dest'" >&2
    echo "$dest"
}

# Make sure tika-app-1.18.jar is present in current directory.
tika_jar="$installdir/tika-app-1.18.jar"
test -s "$tika_jar" || wget  -O "$tika_jar" "http://www-eu.apache.org/dist/tika/tika-app-1.18.jar"

for file; do



# detect file type

if file "$file" | fgrep -q 'PDF document'
then
	target=`make_path "$file" "pdf"`
	bzip2 -q -t "$target" 2>/dev/null || bash "$installdir"/pdf-extract-text-bbox.sh "$installdir" "$file" | bzip2 > "$target"
elif file "$file" | egrep -q 'DjVu.*document'
then
	target=`make_path "$file" "djvu"`
	bzip2 -q -t "$target" 2>/dev/null || bash "$installdir"/djvu-extract-text-bbox.sh "$installdir" "$file" | bzip2 > "$target"
elif file "$file" | egrep -q '(EPUB|Microsoft.*Word|MS Windows HtmlHelp Data|Rich Text Format data)'
then
	target=`make_path "$file" "tika"`
	bzip2 -t "$target" 2>/dev/null || java -jar "$tika_jar" --text "$file" 2>/dev/null | bzip2 > "$target"
else
	echo "Error: Unrecognized document type (not PDF or DJVU or EPUB or DOC or CHM)" >&2
fi

done
