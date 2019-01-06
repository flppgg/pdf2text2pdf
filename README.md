# pdf2text2pdf
## scripts to extract text layer from PDFs and rebuild lighter PDFs 



These scripts were developed to:
1. extract Unicode text from a PDF file (or DjVu file), with the position and size of every word in every page, and 
2. re-build a lighter version of the PDF file that ONLY includes the text layer



This allows you to substantially reduce the size of the PDF file, and potentially to implement full text search functionalities.

The first folder, **pdf2text**, includes a number of Perl and shell scripts to extract the text layer from a PDF or DjVu file, and return a text file with the position and size of every word in the PDF.

The second folder, **text2pdf**, contains a Python script to build a PDF file from such text file.



The Python script is still a beta version that needs testing fixing. In theory it should support every language included in UTF-8, although this is still far away.
