This script builds a PDF file from a text file in the format produced by pdf2text.

You will need to install a Python library called ReportLab. Run this from terminal if you have Python 3 installed (please note that the script only works with Python 3):

```
pip install reportlab
```
or
```
pip3 install reportlab
```


The script processes every file it finds in the folder you indicate. If you run:

```
python3 text2pdf.py /path/to/folder/
```

It will create a new PDF folder in that path and put all the converted PDFs there. Don't forget the "/" at the end or it won't work.
The script also gives some info on the files, for example:

```
Starting.. There are 3 files in this folder, 3 are non-empty, 28.343 MB.
using Font Arial Unicode MS // this is the default font.

first_file_name.djvu.ft //name of the file it is about to process

OCR positions seem not to be precise, I will try to adjust positions //means it will try to fix the y coordinate of words to make lines more straight, if it finds the positions are imprecise
font sizes seem not to be precise, I will try to adjust font sizes //same, but with font sizes
adjusting y_tolerance, trying again with this file //if it finds that lines are broken up, it starts again with a slightly different y_tolerance parameter
OCR positions seem not to be precise, I will try to adjust positions
font sizes seem not to be precise, I will try to adjust font sizes

file_overlaps: 121 // this gives you an idea of how many word overlaps (one word drawn on top of another) there are in the file. just for debugging, and it's not very precise
font might be too big flags: 55  // this also looks at overlaps, but these overlaps most likely are caused by the font being too large compared to the original book font.
file_bad_fonts (TOFU): 11  //this tells you how many characters it was not able to draw, because the utf-8 character did not have a glyph in the Font file you provided. If you are using Arial Unicode MS, and you not using a rare language, it means most likely the character was a bad OCR recognition
File no. 1: success
```
