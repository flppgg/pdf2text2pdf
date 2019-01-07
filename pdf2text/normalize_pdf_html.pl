# This will be used to compress info of the form
# <word xMin="377.700000" yMin="611.820000" xMax="379.700000" yMax="623.820000">%</word>
# into
# 377.7	611.82	2.0	12.0	word
# and <page width="482.000000" height="686.000000"> into 
# 0	0	482.0	686.0
#

while(<>){
    # only print info about words and pages
    if (m|^\s*<word xMin="([-0-9.]+)" yMin="([-0-9.]+)" xMax="([-0-9.]+)" yMax="([-0-9.]+)">(.*)</word>$|) {
	$xmin="$1";
	$ymin="$2"; 
	$xmax="$3";
	$ymax="$4"; 
	$word="$5";
	$xmin =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$ymin =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$dx = sprintf("%.8f", $xmax - $xmin);
	$dx =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$dy = sprintf("%.8f", $ymax - $ymin);
	$dy =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$_ = "$xmin\t$ymin\t$dx\t$dy\t$word\n";
	print;
    }

    if (m|^\s*<page width="([-0-9.]+)" height="([-0-9.]+)">.*$|) {
	$w="$1";
	$h="$2";
	$w =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$h =~ s/\.(\d*[1-9]|0)0*$/.$1/;
	$_ = "0\t0\t$w\t$h\n";
	print;
    }

}

