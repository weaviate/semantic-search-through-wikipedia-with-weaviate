"""
This script processes the Wikipedia datadump
"""

from xml.dom import minidom
import os
import re
import json
import mwparserfromhell


def is_redirect(page):
    """
    Checks if a page is a redirect
    
    Returns
    --------
    bool
        True if the page is a redirect
        False if the page is not a redirect
    """
    redirect = page.getElementsByTagName('redirect')
    if len(redirect) > 0:
        return True
    return False


def contains_all_value(page):
    """
    Validate if both title and text are set
    
    Returns
    --------
    bool
        True if all values are set
        False if not all values are set
    """
    if len(page.getElementsByTagName('title')) == 0:
        return False
    if len(page.getElementsByTagName('text')) == 0:
        return False
    return True


def get_crefs(element):
    """
    Gets all the crossrefs that an article has
    
    Returns
    --------
    array
        An array of crefs to other wikipedia pages
    """

    returnList = []
    text = element[0].firstChild.nodeValue
    crefs = re.findall('\[\[.*?\]\]', text)
    for cref in crefs:
        cref_parsed = cref[2:-2].split("|")
        if ":" not in cref_parsed[0]:
            if len(cref_parsed) == 1:
                cref_final = cref_parsed[0].replace(" ", "_")
            else:
                cref_final = cref_parsed[1].replace(" ", "_")
            if check_file(cref_final) == True:
                returnList.append(cref_final)
    return list(dict.fromkeys(returnList))
    

def clean_line(line):
    """
    Cleans a string from HTML tags and Wiki markup
    
    Returns
    --------
    str
        Returns a string that is cleaned
    """

    refs = re.findall('\<ref.*?\<\/ref\>', line)
    for ref in refs:
        line = line.replace(ref, " ")
    # remove all <ref/>'s
    refs = re.findall('\<ref.*?\/\>', line)
    for ref in refs:
        line = line.replace(ref, " ")
    # remove all <math
    tags = re.findall('\<math.*?\<\/math\>', line)
    for tag_match in tags:
        line = line.replace(tag_match, "")
    # remove all inline {{ }}'s
    brackets = re.findall('\{\{.*?\}\}', line)
    for bracket_match in brackets:
        line = line.replace(bracket_match, "")
    # remove all inline {| |}'s
    brackets = re.findall('\{\|.*?\|\}', line)
    for bracket_match in brackets:
        line = line.replace(bracket_match, "")
    # replace brackets
    line = line.replace("'''", "")
    # remove crefs with locations
    crefs = re.findall('\[\[.*?\]\]', line)
    for cref in crefs:
        cref_parsed = cref[2:-2].split("|")
        line = line.replace(cref, cref_parsed[-1])
    # remove cref brackets (left overs)
    line = line.replace("[[", "").replace("]]", "")
    # remove HTML notes (inline)
    refs = re.findall('\<\!--.*?\--\>', line)
    for ref in refs:
        line = line.replace(ref, " ")
    # remove thumb| |
    brackets = re.findall('thumb\|.*?\|', line)
    for bracket_match in brackets:
        line = line.replace(bracket_match, "")
    # remove thumb|
    line = line.replace("thumb|", "")
    return line


def is_title(line):
    """
    Checks if a line contains a Wiki title
    
    Returns
    --------
    bool
        True if the line contains a title
        False if the line does not contains a title
    """

    if len(line) > 3 and line[-2:] == "==":
        return line.replace("=", "")[:-1]
    return None


def should_include_paragraph(title, count):
    """
    Validates if a paragraph is relevant for semantic search queries
    
    Returns
    --------
    bool
        True if the paragraph should be included
        False if the paragraph should not be included
    """

    if title == "" and count > 0:
        return False
    elif title.startswith("Reference"):
        return False
    elif title.startswith("External link"):
        return False
    elif title.startswith("General reference"):
        return False
    elif title.startswith("Further readin"):
        return False
    elif title.startswith("See als"):
        return False
    elif title.startswith("Other uses"):
        return False
    elif title.startswith("Subdivision"):
        return False
    elif title.startswith("Citation"):
        return False
    elif title.startswith("Review"):
        return False
    elif title.startswith("Sources"):
        return False
    elif title.startswith("Note"):
        return False
    return True


def get_clean_paragraph(count):
    """
    Creates a clean paragraph dict
    
    Returns
    --------
    dict
        A dict with title, content en the count
    """

    return {
        "title": "",
        "content": "",
        "count": count
    }


def get_paragraphs(element):
    """
    Creates an array of paragraphs related to an article
    
    Returns
    --------
    array
        An array with paragraphs related to an article
    """

    return_list = []
    text = element[0].firstChild.nodeValue
    paragraph_text = ""
    count = 0
    paragraph = get_clean_paragraph(count)
    for line in text.split('\n'):
        parsed_text = mwparserfromhell.parse(line)
        if line.strip().startswith('=='):
            if paragraph["content"] != "" and should_include_paragraph(paragraph["title"], count) == True:
                paragraph["content"] = clean_line(paragraph["content"])
                if count == 0:
                    del(paragraph["title"])
                return_list.append(paragraph)
            count += 1
            paragraph = get_clean_paragraph(count)
            paragraph["title"] = parsed_text.strip_code().strip()
        else:
            process_content = parsed_text.strip_code().strip()
            if process_content != "" and "|" not in process_content and "{{" not in process_content and "}}" not in process_content:
                paragraph["content"] += process_content + " "
    return return_list


def process_page(i):
    """
    Processes a complete article page
    
    Returns
    --------
    dict
        A dict with a title, crefs and an array of paragraphs
    """

    page = minidom.parseString(i)
    if is_redirect(page) == True:
        return None
    elif contains_all_value(page) == True:
        return {
            "title": page.getElementsByTagName('title')[0].firstChild.nodeValue,
            "crefs": get_crefs(page.getElementsByTagName('text')),
            "paragraphs": get_paragraphs(page.getElementsByTagName('text'))
        }


def create_file(name):
    """
    Creates an empty file with page names
    This is used to validate if a page exists
    """

    try:
        if ":" not in name:
            open("available_pages/" + name.replace("/", "___"), "a")
    except:
        pass


def check_file(name):
    """
    Validates if a file exsists
    
    Returns
    --------
    bool
        True if a file exists
        False if a file does not exist
    """
    return os.path.exists("available_pages/" + name.replace("___", "/"))


def get_available_pages(filename):
    """
    Collects all available pages
    """

    print("Collect available pages")
    if not os.path.exists("available_pages"):
        os.mkdir("available_pages")
    counter = 0
    with open(filename) as file_in:
        page = ""
        for line in file_in:
            page += line
            if "<page>" in line:
                page = line
            elif "</page>" in line:
                page_dom = minidom.parseString(page)
                redirect = page_dom.getElementsByTagName("redirect")
                if len(redirect) == 0 and len(page_dom.getElementsByTagName('title')) > 0:
                    create_file(page_dom.getElementsByTagName('title')[0].firstChild.nodeValue.replace(" ", "_"))
                    counter += 1
                    if (counter % 2500) == 0:
                        print("Added to Array", counter)


def process_pages(filename):
    """
    Processes all available pages
    """

    counter = 0
    counter_paragraphs = 0
    print("Process available pages")
    with open(filename) as file_in:
        page = ""
        for line in file_in:
            page += line
            if "<page>" in line:
                page = line
            elif "</page>" in line:
                try:
                    parsed_page = process_page(page)
                    if parsed_page != None:
                        with open("articles.json", "a") as articles_file:
                            articles_file.write(json.dumps(parsed_page) + "\n")
                        counter += 1
                        counter_paragraphs += len(parsed_page["paragraphs"])
                        print(counter, 'written:', parsed_page["title"], "with a total of", counter_paragraphs, "paragraphs")
                except:
                    print('error')
                    pass


if __name__ == "__main__":
    """
    Main function
    """
    filename = "latest-pages-articles.xml"
    # Get all the pages and store names as files
    get_available_pages(filename)
    # Process the pages and output a JSON file
    process_pages(filename)
