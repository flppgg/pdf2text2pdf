
#TO TEST THE SCRIPT WITH LIBERATION FONT, DO NOT CHANGE ANYTHING, 
#JUST PLACE THE FILE "LiberationSerif-Regular.ttf" and "LiberationSansNarrow-Regular.ttf"
#IN THE SAME FOLDER AS THIS SCRIPT

default_path_to_font_file = "ARIALUNI.TTF" #put the path to the TTF font file here if you want to change font
default_font_name = "Arial Unicode" #change it to the name of the font you decide to use (mainly for console logging)

backup_path_to_font_file = "LiberationSerif-Regular.ttf" 
backup_font_name = "Liberation Serif Regular" 

narrow_path_to_font_file = "LiberationSansNarrow-Regular.ttf"
narrow_font_name = "Liberation Sans Narrow"


from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black, red
from collections import Counter
from html import unescape
from time import time
import sys, os


class ErrorYTolerance(Exception):
    pass
class ErrorGoToNextFile(Exception):
    pass
class ErrorOverlap(Exception):
    pass
class ErrorBadFont(Exception):
    pass

class flags_class():
    def __init__(self):
        self.book_length = 0
        self.total_bad_fonts = 0
        self.file_bad_fonts = 0
        self.total_overlaps = 0
        self.file_overlaps = 0
        self.y_tolerance_flags = 0
        self.other_flag = 0
        self.y_order_correct = True
        self.adjust_font_sizes = True
        self.font_might_be_too_big_flags = 0
        self.remembered_page = 0
        self.use_narrow_font = False
        self.keep_regular_font = False

    def set_book_length(self, str):
        self.book_length = int(str.strip())

    def raise_other_flag(self):
    	self.other_flag += 1

    def raise_font_might_be_too_big_flag(self):
        self.font_might_be_too_big_flags += 1

    def set_use_narrow_font(self):
        self.use_narrow_font = True

    def set_keep_regular_font(self):
        self.keep_regular_font = True
    
    def remember_this_page(self, int):
    	self.remembered_page = int

    def check_font_sizes(self, page_words): #most likely, this goes hand in hand with ocr positioning precision
        last, sames, similars = 0, 0, 0
        for x in page_words:
            this = x[3]
            if last:
                if last * 0.9 < this < last * 1.1:
                    if this == last:
                        sames += 1
                    else:
                        similars += 1
            last = x[3]
        if sames >= similars * 3: 
            print('font sizes seem to be precise, I will not adjust font sizes')
            self.adjust_font_sizes = False
        else:
            print('font sizes seem not to be precise, I will try to adjust font sizes')
            self.adjust_font_sizes = True


    def set_y_order(self, page_words): #find out if y coordinates start from bottom or top
        first_ys = [x[1] for x in page_words[:5]]
        first_ys_average = sum(x for x in first_ys) / len(first_ys)
        last_ys = [x[1] for x in page_words[-5:]]
        last_ys_average = sum(x for x in last_ys) / len(last_ys)
        if first_ys_average > last_ys_average:
            self.y_order_correct = True
        else:
            self.y_order_correct = False
        
    def check_font(self, str, font_widths): #Check if the font in use has a glyph for this Unicode string. If not, add a TOFU flag
        for char in str:
            if ord(char) in font_widths:
                pass
            else:
                self.file_bad_fonts += 1
                self.total_bad_fonts += 1
            if self.file_bad_fonts == 100000: #value set unrealistically high. If you want the script to stop running when there are too many TOFU in one file, set it lower
                raise ErrorBadFont

    def reset_file_flags(self):
        self.file_bad_fonts = 0
        self.file_overlaps = 0
        self.y_tolerance_flags = 0
        self.adjust_font_sizes = True
        self.font_might_be_too_big_flags = 0
        self.use_narrow_font = False
        self.keep_regular_font = False

    def reset_page_flags(self):
        self.y_tolerance_flags = 0  

    def raise_y_tolerance_flag(self):
        self.y_tolerance_flags += 1

    def add_one_overlap(self):
        self.total_overlaps += 1
        self.file_overlaps += 1

    def find_overlaps(self, squares_taken, square_vertices, lines_to_reduce): #attempts to find out when one word is drawn on another word, raises a file_overlap flag

        for square in squares_taken:
            square_vertices.append([square[0], square[2], square[4]])
            square_vertices.append([square[1], square[3], square[4]])
            square_vertices.append([square[0], square[3], square[4]])
            square_vertices.append([square[1], square[2], square[4]])
            square_vertices.append([square[0], (square[3]-square[2])/2, square[4]])
            square_vertices.append([square[1], (square[3]-square[2])/2, square[4]])
            square_vertices.append([(square[1]-square[0])/2, (square[3]-square[2])/2, square[4]])
            

        for vertex in square_vertices:
            for square in squares_taken:
                if 1.05 * square[2] < vertex[1] <  0.95 * square[3]: 
                    if 1.05 * square[0]< vertex[0] <  0.95 * square[1]:
                        self.total_overlaps += 1
                        self.file_overlaps += 1

                        lines_to_reduce.append(square[4]) #these are the indexes of the lines that have a vertex in another square

                
flags_wizard = flags_class()   

def set_fonts():
    global font_widths
    global font_name

    if flags_wizard.use_narrow_font == True and flags_wizard.keep_regular_font == False:
        font_name = narrow_font_name
        font = TTFont(font_name, narrow_path_to_font_file)
        print('using narrow font ' + font_name)

    else:
        if os.path.isfile(default_path_to_font_file):
            font_name = default_font_name
            font = TTFont(font_name, default_path_to_font_file)
            print('using Font ' + default_font_name)

        else:
            print('could not find ' + default_font_name + '. Falling back to ' + backup_font_name + '. Many Unicode Characters will become TOFU')
            font_name = backup_font_name
            font = TTFont(font_name, backup_path_to_font_file)

    registerFont(font)
    font_widths = font.face.charWidths



def set_y_tolerance_and_top(filename): # finds out when a book will have wobbly lines
    global y_tolerance
    global how_many_y_adjusted
    
    with open(path + filename,'r', encoding = 'utf-8', errors = 'ignore') as r:
        count = 0
        for line in r:
            if len(line.split('\t')) == 4:
                if count > 200:
                    break
                count = 0
                page_words = []
            elif len(line.split('\t')) == 5:
                page_words.append(line.split('\t'))
                count += 1
            elif len(line.split('\t')) == 1:
                pass
            else:
                pass

    if count == 0:
        raise ErrorGoToNextFile

    try:
        page_words = [[float(x[0]), float(x[1]), float(x[2]), float(x[3]), x[4].strip()] for x in page_words]
    except UnboundLocalError:
        raise ErrorGoToNextFile  # this happens when the file is empty. 
    
    last, sames, similars = 0, 0, 0
    for x in page_words:
        this = x[1]
        if last:
            if last * 0.96 < this < last * 1.04:
                if this == last:
                    sames += 1
                else:
                    similars += 1
        last = x[1]
    if sames >= similars * 1.5: 
        print('OCR positions seem to be precise, I will not adjust positions')
        y_tolerance = 0
        
    else:
        print('OCR positions seem not to be precise, I will try to adjust positions')
        y_tolerance = 0.012 #set the tolerance to determine if words are on the same line
        how_many_y_adjusted +=1
    
    if y_tolerance_errors > 0: #this is to control y_tolerance in case an ErrorYTolerance was raised. the script will start again with this file, using a higher y_tolerance
        y_tolerance = y_tolerance + y_tolerance_errors * 0.004
        print(y_tolerance)

    flags_wizard.set_y_order(page_words)
    flags_wizard.check_font_sizes(page_words)
    


def fix_overlaps(lines_to_reduce, page_lines): #good idea, but doesn't seem to work very well. Not in use
    for line in lines_to_reduce:
        page_lines[line][1] = page_lines[line][1] * 0.9


def draw_red_squares(lines_to_reduce, page_lines, squares_taken, can): #draws red squares around the overlapping words, so that they can be easily spotted. Works on about 50% of the overlaps
    can.setFillColor(Color(100,0,0, alpha=0.5))
    for line in lines_to_reduce:
        sq = squares_taken[line]
        can.rect(sq[0], sq[2], sq[1]-sq[0], sq[3]-sq[2], fill = True, stroke = False)
        #square = [x, x1, y, y1, line_index]
    can.setFillColor(black)


def is_paragraph(line_list, page_data):  #finds out if the line is in a paragraph with the previous lines. If yes, it uses the same font size
    p_tol = 0.01

    if len(page_data[2]) > 3 and len(line_list) > 2: 

        previous_lines = [page_data[2][-1], page_data[2][-2], page_data[2][-3], page_data[2][-4]]

        lines_in_paragraph = (previous_lines[0] * (1 - p_tol) < line_list[0][0] < previous_lines[0] * (1 + p_tol) 
            + previous_lines[1] * (1 - p_tol) < line_list[0][0] < previous_lines[1] * (1 + p_tol)
            + previous_lines[2] * (1 - p_tol) < line_list[0][0] < previous_lines[2] * (1 + p_tol)
            + previous_lines[3] * (1 - p_tol) < line_list[0][0] < previous_lines[3] * (1 + p_tol))
       
        if lines_in_paragraph > 1:

            return True

        elif lines_in_paragraph == 1:

            if len(page_data[2]) > 4:

                previous_lines.append(page_data[2][-5])
                previous_lines.append(page_data[2][-6])

                if (previous_lines[4] * (1 - p_tol) < line_list[0][0] < previous_lines[4] * (1 + p_tol) 
                    + previous_lines[5] * (1 - p_tol) < line_list[0][0] < previous_lines[5] * (1 + p_tol)
                    > 0):

                    return True
            else:
                return False
        else:
            return False
    else:
        return False


def set_font_size(line_list, page_data, prec_i):  #routine to calculate font size of line
    
    line_font = sum(ii[3] for ii in line_list) / len(line_list)

    if flags_wizard.adjust_font_sizes == True:

        line_length_theory = prec_i[0] + prec_i[2] - line_list[0][0] 
        line_length_practice = stringWidth(' '.join(ii[4] for ii in line_list), font_name, line_font)

        if line_length_practice:
            scale_factor = line_length_theory / line_length_practice  
        else:
            scale_factor = 1

        if len(page_data[1]) > 7: #if there are a few words in the page already, it uses the page average font size to understand what it's going on

            if line_font < page_data[0] * 0.7 and scale_factor > 1: #if it's smaller than average, it can do what it wants up to page average

                if line_font * scale_factor < page_data[0]:

                    line_font = scale_factor * line_font
                    
                else:

                    line_font = page_data[0]     

            elif ((scale_factor > 1.7 and len(line_list) < 3) 
                or line_font > page_data[0] * 1.3
                or scale_factor > 2):

                line_font = line_font

            else:
                line_font = line_font * scale_factor

        else: #for the first 7 lines of a page, 
            if 0.4 < scale_factor < 1.8:
                line_font = scale_factor * line_font

        try:
            last_font = page_data[1][-1]

            if last_font < line_font < last_font * 1.1:
                line_font = last_font

        except IndexError:
            pass
    else:
    	if len(page_data[1]) > 7 and line_font > page_data[0] * 2.5: #words that big are probably a mistake, so this reduces them
            line_font = page_data[0] * 1.5

    return line_font



def if_lines_have_same_y(line_font, line_list, page_data, y_tolerance, end_of_last_line, y_origin, i_float, page_size, page_index): 

    #this checks a number of things in case this "line" is actually probably on the same line as the last
    if (line_list[0][0] >= end_of_last_line[0] 
    and end_of_last_line[1] * (1 - 0.017) < y_origin < end_of_last_line[1] * (1 + 0.017)
    and y_tolerance != 0): #raising a flag, if there are too many flags it means probably y_tolerance is too low and lines are wobbly
        
        flags_wizard.raise_y_tolerance_flag()
            
        if (len(page_data[1]) > 2
            and line_font > page_data[1][-1] * 1.3): 
                line_font = page_data[1][-1] #if line font is bigger than the previous line, probably there is something wrong, reduce it

    if flags_wizard.adjust_font_sizes == False:
    # this seems to be working, it finds out when something fucks up and one line ends over the next line, because the font was too big.
    
        double_check = stringWidth(' '.join(ii[4] for ii in line_list), font_name, line_font)

        if line_list[0][0] < i_float[0] < line_list[0][0] + double_check:
            y_origin_1 = i_float[1]
	        
            if flags_wizard.y_order_correct == False:
                y_origin_1 = page_size[1] - y_origin_1

            if y_origin * (1 - y_tolerance - 0.004) <= y_origin_1 <= y_origin * (1 + y_tolerance + 0.004):


                if i_float[0] + i_float[2] < line_list[0][0] + double_check: # it is a bad overlap, possibly just a character in the wrong place, difficult to fix
                    flags_wizard.add_one_overlap() #what could be a solutionn?

                else:
                    flags_wizard.raise_font_might_be_too_big_flag()
                    line_list[0].append('red')

                if page_index > flags_wizard.book_length / 4 and flags_wizard.font_might_be_too_big_flags >= page_index * 2:
                    

                    if overlap_errors < 1:
                        flags_wizard.remember_this_page(page_index)
                        
                        raise ErrorOverlap

                    elif overlap_errors == 1: #i've already tried to change font...
                        if page_index > flags_wizard.remembered_page * 1.1: # ...and it's working
                            pass # so keep going!

                        else: # ...and it hasn't worked
                            raise ErrorOverlap

                        #REDUCING FONT SIZE IS USELESS, I HAVE PROOF. 
                        #if flags_wizard.remembered_page != page_index or flags_wizard.file_overlaps < 30: #either there's been a significant reduction in overlaps, or there's not many rectangle overlaps (which means the file is probably not a mess)   
                        #    raise ErrorOverlap



def set_y_origin(line_list, page_size): #find out if y coordinates are counted from the top or the bottom of the page

    y_origin = sum(ii[1] for ii in line_list) / len(line_list)

    if flags_wizard.y_order_correct == False:
        y_origin = page_size[1] - y_origin

    return y_origin


def write_page(page_lines, textobj, line_list, page_data, page_size, prec_i): #writes the past page

    for line in page_lines:

        x_origin = line[0][0][0]
        final_font_size = line[1]
        textobj.setTextOrigin(x_origin, line[2])      
        textobj.setFont(font_name, final_font_size)

        if len(line[0][0]) == 6: 

            final_font_size = final_font_size * 0.93
            textobj.setFont(font_name, final_font_size)
               
            textobj.setFillColor(red)
     
            textobj.textOut(' '.join(ii[4] for ii in line[0]))
            textobj.setFillColor(black)
        else:    
            textobj.textOut(' '.join(ii[4] for ii in line[0]))
    
    #write the last line of the page
    x_origin = line_list[0][0]
    y_origin = set_y_origin(line_list, page_size)

    if is_paragraph(line_list, page_data):
        line_font = page_data[1][-1]
    else:
        line_font = set_font_size(line_list, page_data, prec_i)

    line_font = line_font * (1 - overlap_errors * 0.12)
    
    textobj.setTextOrigin(x_origin, y_origin)  
    textobj.setFont(font_name, line_font)     
    textobj.textOut(' '.join(ii[4] for ii in line_list))   



def processing(filename):  #where most of the processing happens

    with open(path + filename,'r', encoding = 'utf-8', errors = 'ignore') as r:
        can = canvas.Canvas(path + 'PDFs/' + filename + '.pdf')
        
        for l in r:
            i = l.split('\t')

            if len(i) == 5: # means this is just a word in the page
                
                if new_page == False: #this is every word in the page BUT the first
                    
                    i_float = [float(i[0]), float(i[1]), float(i[2]), float(i[3]), unescape(i[4].strip())]

                    flags_wizard.check_font(i_float[4], font_widths)

                    prec_y = prec_i[1] # coordinates of previous word
                    prec_x = prec_i[0] + prec_i[2]
                    
                    if (prec_x < i_float[0]  
                        and prec_y * (1 - y_tolerance) <= i_float[1] <= prec_y * (1 + y_tolerance)  # is the word on the same line as the last?
                        and len(i_float[4]) > 1 # this was added to solve messing up math formulas, which often have one character lines
                        and (i_float[0] - prec_x) < reasonable_space):  #this was added to solve messup in indexes at beginning of books or bunching up of lines
                        
                        line_list.append(i_float)
                        
                    else: #this is not the same line. I will write the past line, then I will initiate a new line_list and append this first word
                        
                        y_origin = set_y_origin(line_list, page_size)

                        if is_paragraph(line_list, page_data):
                            line_font = page_data[1][-1]
                        else:
                            line_font = set_font_size(line_list, page_data, prec_i)
           
                        #this checks a number of things in case this "line" is actually probably on the same line as the last
                        if_lines_have_same_y(line_font, line_list, page_data, y_tolerance, end_of_last_line, y_origin, i_float, page_size, page_index)
                        

                        #page_data = [font average,[line_font1,line_font2 ...],[x origins for paragraph], page number]
                        page_data[1].append(line_font)
                        page_data[2].append(line_list[0][0])
                        page_data[0] = sum(f for f in page_data[1]) / len(page_data[1])

                        
                        page_lines.append([line_list, line_font, y_origin])
                                             
                        #square = [x, x1, y, y1, line_index]
                        line_length_final = stringWidth(' '.join(ii[4] for ii in line_list), font_name, line_font)
                        square = [line_list[0][0], line_list[0][0] + line_length_final, y_origin, y_origin + line_font, len(page_data[1])-1]
                        squares_taken.append(square)

                        end_of_last_line = []
                        end_of_last_line.append(line_list[-1][0] + line_list[-1][2])
                        end_of_last_line.append(y_origin)
                        
                        line_list = []
                        line_list.append(i_float)

                else: #if this is the first word in the page
                    new_page = False
                    line_list = []
                    i_float = [float(i[0]), float(i[1]), float(i[2]), float(i[3]), i[4].strip()]
                    line_list.append(i_float)
                    prec_i = i_float
                    continue

                prec_i = i_float


                
            elif len(i) == 4: #means this is the beginning of a new page. Write the past page to pdf file
                
                if first_page:
                    first_page = False
                    page_index = 0

                else:
                    if len(page_lines): #some pages are just white pages

	                    reasonable_space = stringWidth('   ', font_name, page_data[0]) #using the average font size of previous page to check for next page lines..

	                    if len(page_data[1]) > 20:
	                        if flags_wizard.y_tolerance_flags > len(page_data[1]) * 0.3:
	                            if y_tolerance_errors == 1:
	                                pass
	                            else:
	                                raise ErrorYTolerance
	                    
	                    flags_wizard.find_overlaps(squares_taken, square_vertices, lines_to_reduce)
	                    #fix_overlaps(lines_to_reduce, page_lines) NOT IN USE NOW
	                    draw_red_squares(lines_to_reduce, page_lines, squares_taken, can)
	                
	                    write_page(page_lines, textobj, line_list, page_data, page_size, prec_i)


                can.drawText(textobj)
                can.showPage()

                page_index +=1
                
                page_size = (int(float(i[2])), int(float(i[3])))
                can.setPageSize(page_size)
                textobj = can.beginText()
                
                flags_wizard.reset_page_flags()
                prec_i = [0,0,0,0,0]
                new_page = True
                page_data = [0,[],[]]
                  
                end_of_last_line = []
                end_of_last_line.append(99999999) #fake, just to avoid some conditions verifying from last line of one page to first line in next page
                end_of_last_line.append(99999999) 
                squares_taken = []
                square_vertices = []
                page_lines = []
                lines_to_reduce = []
            
            elif len(i) == 1: #means this is the beginning of the document
                can.setPageSize((1,1))
                textobj = can.beginText()
                first_page = True
                flags_wizard.set_book_length(i[0])

                reasonable_space = stringWidth('   ', font_name, 40) # this is to start off, using a large font which will be adapted to file font size average
        

        #write the last page of file
        write_page(page_lines, textobj, line_list, page_data, page_size, prec_i)
        can.drawText(textobj)
        
        can.setTitle(filename)
        can.save()




def run(filename):  
    set_fonts()
    set_y_tolerance_and_top(filename)
    processing(filename)
    

##################################################################PROGRAM STARTS HERE

dirty_files = []
path = sys.argv[1] #IN THE FORMAT /path/to/text_files_folder/
for (dirpath, dirnames, filenames) in os.walk(path):
    dirty_files.extend(filenames)
    break

try:
    os.mkdir(path+'PDFs')
except FileExistsError:
    pass

size_MB = 0
clean_files= []
for f in dirty_files:
    size = os.path.getsize(path+f)
    if size != 0:
        clean_files.append(f)
        size_MB += size / 1000000
files = clean_files

print('Starting.. There are ' + str(len(dirty_files)) + ' files in this folder, '
    +str(len(clean_files)) + ' are non-empty, '
    +str(size_MB) + ' MB.')

files_count = 0
start_time = time()
how_many_y_adjusted = 0
list_of_poor_quality_files = []

for filename in files:
    print('\n'+filename)
    y_tolerance_errors = 0
    overlap_errors = 0
    
    while y_tolerance_errors < 2 and overlap_errors < 3:
        
        try:
            run(filename)

            flags_wizard.total_overlaps += flags_wizard.font_might_be_too_big_flags
            print('file_overlaps: ' + str(flags_wizard.file_overlaps))
            print('file_bad_fonts (TOFU): ' + str(flags_wizard.file_bad_fonts))
            print('font might be too big flags: ' + str(flags_wizard.font_might_be_too_big_flags))
            print('other flags: ' + str(flags_wizard.other_flag))
            print('File no. '+str(files_count)+': success')

            if flags_wizard.file_overlaps > 100:
                list_of_poor_quality_files.append(filename)

            flags_wizard.reset_file_flags()
            break
        
        except ErrorYTolerance:
            y_tolerance_errors += 1
            print('adjusting y_tolerance, trying again with this file..')
            flags_wizard.reset_file_flags()
        
        except ErrorGoToNextFile:
            print('Broken file')
            flags_wizard.reset_file_flags()
            break

        except ErrorOverlap:
            if overlap_errors == 0:
                print('found more than ' + str(flags_wizard.font_might_be_too_big_flags) + 
                ' overlaps, changing font type and trying again..')
                flags_wizard.reset_file_flags()
                flags_wizard.set_use_narrow_font()
            if overlap_errors == 1:
                print('narrow font is not helping, reverting to regular font (more legible)')
                flags_wizard.reset_file_flags()
                flags_wizard.set_keep_regular_font()
            overlap_errors += 1

        except ErrorBadFont:
            print('Error, the current font cannot handle many unicode characters in the file. Please change font')
            flags_wizard.reset_file_flags()
            break
    files_count+=1

        
seconds_taken = time() - start_time
seconds_per_file = seconds_taken / files_count
seconds_per_MB = seconds_taken / size_MB

print('\n\nFinished, processed ' + str(files_count) + ' out of ' + str(len(dirty_files)) + ' files. '
    +str(how_many_y_adjusted) + ' y_adjustments were made. '
    +str(flags_wizard.total_overlaps) + ' overlaps. '
    +str(flags_wizard.total_bad_fonts) + ' bad fonts (TOFU). '
    +str(seconds_per_file) + ' seconds per file. '
    +str(seconds_per_MB) + ' seconds per MB.')

print('\nThe layout of the following files is likely to be of poor quality:\n')
for i in list_of_poor_quality_files:
    print(i)


