# This will be used to compress info of the form
# (word 377 611 397 yMax=623 "word"))))
# into
# 377.7	611.82	377.7	623.26	word
# and (page 0 0 482 686
# 0	0	482 686">
#

while(<>){
    # only print info about words and pages
    if (m|^\s*\(word ([-0-9]+) ([-0-9.]+) ([-0-9.]+) ([-0-9.]+) "(.*)"\)*$|) {
	$xmin="$1";
	$ymin="$2";
	$xmax="$3";
	$ymax="$4";
	$word="$5";
	$dx = sprintf("%d", $xmax - $xmin);
	$dy = sprintf("%d", $ymax - $ymin);
	$word =~ s/\\([0-3][0-7][[0-7])/pack("c", oct($1));/ge;
	$_ = "$xmin\t$ymin\t$dx\t$dy\t$word\n";
	print;
    }

    if (m|^\s*\(page ([-0-9]+) ([-0-9]+) ([-0-9]+) ([-0-9]+).*$|) {
	$xmin="$1";
	$ymin="$2";
	$xmax="$3";
	$ymax="$4";
	$dx = sprintf("%d", $xmax - $xmin);
	$dy = sprintf("%d", $ymax - $ymin);
	$_ = "$xmin\t$ymin\t$dx\t$dy\n";
	print;
    }
}

