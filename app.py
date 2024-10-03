from flask import Flask, request, render_template
import re

app = Flask(__name__)

# Regex to check if a line already has <translate> tags
translate_tag_pattern = re.compile(r"<translate>.*</translate>")
# Regex to match attributes like rowspan, colspan, etc.
attribute_pattern = re.compile(r"\b\w+=[^\s\|]+")
# Regex to detect table cell separators (| and ||)
table_cell_separator_pattern = re.compile(r"(\|\||\||\*)")
# Regex to detect headers in the format of == Header ==
header_pattern = re.compile(r"^(={2,})(.*?)(={2,})$")
# Regex to detect table header cell separators (! and !!)
header_cell_separator_pattern = re.compile(r"(!{1,2})")

def add_translate_tags(text):
    """
    Wraps the text in <translate> tags if it doesn't already have them
    and if it is not an attribute like rowspan=11.
    """
    if attribute_pattern.search(text):
        return text
    if not translate_tag_pattern.search(text) and text.strip():
        return f'<translate>{text.strip()}</translate>'
    return text

def process_table_line(line):
    """
    Processes a single line of a table and adds <translate> tags where necessary,
    ensuring that only the actual content of table cells is wrapped, not the separators.
    """
    if line.startswith("|+"):
        if line[2:].strip() == "":
            return line
        # For table caption
        return f'{line[0:2]}<translate>{line[2:].strip()}</translate>'
    elif line.startswith("|-"):
        # Table row separator
        return line
    elif line.startswith("!"):
        # For table headers, split on ! and !!
        headers = header_cell_separator_pattern.split(line)
        translated_headers = []
        for header in headers:
            if header in ['!', '!!']:  # Preserve the ! and !! without adding translate tags
                translated_headers.append(header)
            else:
                translated_headers.append(add_translate_tags(header))
        return "".join(translated_headers)
    else:
        # For table rows, ensure content is wrapped but separators are untouched
        cells = table_cell_separator_pattern.split(line)
        translated_cells = []
        for cell in cells:
            # print("ok"+cell+" ")
            if cell in ['|', '||','*']:  # Leave separators as is
                translated_cells.append(cell)
            elif cell.startswith("{{"):
                translated_cells.append(cell)
            elif cell.endswith("}}"):
                translated_cells.append(add_translate_tags(cell[:-2])+"}}")
    


            else:
                # Add translate tags around the cell content
                translated_cells.append(add_translate_tags(cell))
        return "".join(translated_cells)

def process_header(line):
    """
    Processes headers (e.g., == Header ==) and adds <translate> tags around the header text.
    """
    match = header_pattern.match(line)
    if match:
        # Extract the equal signs and the header content
        opening_equals = match.group(1)
        header_text = match.group(2).strip()
        closing_equals = match.group(3)
        # Wrap only the header text with <translate> tags, keep the equal signs intact
        return f'{opening_equals} <translate>{header_text}</translate> {closing_equals}'
    return line

def process_double_name_space(line):
    """
    Double Name space (e.g., [[link/eg]]) and adds <translate> tags around the eg text.
    """
    pipestart = False
    returnline = ""
    """
        for file 
    """
    if line[2:6]=="File":
        i=0
        while i < (len(line)):
            if(line[i]=='a' and line[i+1]=='l' and line[i+2]=='t' and line[i+3]=='='):
                returnline+="alt=<translate>"
                i+=4
                while line[i]!='|' and line[i]!=']' :
                    returnline+=line[i]
                    i+=1
                returnline+="</translate>"
                returnline+=line[i]
            else:
                returnline+=line[i]
            i+=1

        return returnline
    
    """
    For normal pipe name spaces
    """

    line1= line[2:-2]
    words = line1.split("|")

    # print(len(words))
    if(len(words)>1):
        returnline+="[["
        returnline+=words[0]+"|"
        words=words[1:]

        for word in words:
            if(word.strip()!=""):
                returnline+="<translate>"
                returnline+=word
                returnline+="</translate>"
            else:
                returnline+="|"
        returnline+="]]"
        return returnline

    else:
        for i in range(len(line)):
            if(line[i]=='|' and pipestart is False):
                pipestart=True
                returnline+="|<translate>"
            
            elif pipestart is True and (line[i]=='|' or line[i]==']' ):
                pipestart=False
                returnline+="</translate>"
                returnline+=line[i]
                if(line[i]=='|'):
                    returnline+="<translate>"
                    pipestart=True
            
            else:
                returnline+=line[i]
        return returnline

def process_external_link(line):
    """
    External link (e.g., [http://example.com]) and adds <translate> tags around the header text.
    """
    words=line.split()
    for i,word in enumerate(words):
        if(i==0):
            continue
        elif(']' in word):
            if len(word[:-1])>0:
                words[i]=f"<translate>{word[:-1]}</translate>]"
        else:
            words[i]=f"<translate>{word}</translate>"
    line=' '.join(words)
    return line
def process_lists(line):
    for i in range(len(line)):
        if line[i]=='*' or line[i]=='#' or line[i]==':' or line[i]==';':
            continue
        else:
            words=line[i:].split("<br>")
            for j in range(len(words)):
                worder=words[j].split(":")
                for k in range(len(worder)):
                    if worder[k]=='':
                        continue
                    else:
                        worder[k]=f"<translate>{worder[k]}</translate>"
                words[j]=":".join(worder)
            newstring="<br>".join(words)
            return f"{line[:i]}{newstring}"
def convert_to_translatable_wikitext(wikitext):
    """
    Converts standard wikitext to translatable wikitext by wrapping text with <translate> tags.
    Handles tables and preserves their structure.
    """
    lines = wikitext.split('\n')
    converted_lines = []

    in_table = False
    in_space_name_single = False
    in_space_name_double = False


    for line in lines:
        line = line.strip()

        if line:
            if line.startswith("{|"):
                in_table = True
                converted_lines.append(line)  # Table start
            elif line.startswith("|}") and in_table:
                in_table = False
                converted_lines.append(line)  # Table end
            elif in_table:
                converted_lines.append(process_table_line(line))
            elif header_pattern.match(line):
                converted_lines.append(process_header(line))  # Process headers
            elif line.startswith("http"):
                converted_lines.append(line)  # the http link 
            elif line.startswith("[["):
                converted_lines.append(process_double_name_space(line))
            elif line.startswith("["):
                converted_lines.append(process_external_link(line))
            elif line.startswith("<nowiki>"):
                converted_lines.append(line)
            elif line.startswith("*") or line.startswith("#") or line.startswith(":") or line.startswith(";"):
                converted_lines.append(process_lists(line))
            else:
                converted_lines.append(add_translate_tags(line))

        else:
            converted_lines.append('')

    return '\n'.join(converted_lines)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/convert', methods=['GET'])
def redirect_to_home():
    return render_template('home.html')

@app.route('/convert', methods=['POST'])
def convert():
    wikitext = request.form.get('wikitext', '')
    converted_text = convert_to_translatable_wikitext(wikitext)
    return render_template('home.html', original=wikitext, converted=converted_text)

if __name__ == '__main__':
    app.run(debug=True)
