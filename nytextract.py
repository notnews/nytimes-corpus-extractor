#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import signal
import logging
import re
import os
import sys
import optparse
import csv
import fnmatch
import tarfile

from lxml import etree

# ===========================================================================================================
# Default configuration
CSV_OUTPUT_FILE       = 'outfile.csv'           # Default CSV output file
TEXT_OUTPUT_DIR       = 'text'                  # Default Text files output directory
MULTIVALUE_SEPARATOR  = '|'                     # Multiple value field separator
EMPTY_VALUE           = 'NA'                    # Empty field value

APPEND_IF_EXIST       = False                   # True or False
# ===========================================================================================================

logger = logging. getLogger ('nytextract')
logger. addHandler (logging. StreamHandler ())
logger. setLevel (logging. DEBUG)
        
usage = "Usage: %prog [options] <xml directory>"
def parse_command_line(argv):
    """Command line options parser
    """
            
    parser = optparse.OptionParser(add_help_option=True, usage=usage)
    
    parser.add_option("-a", "--append", action="store_true", dest="append", default=APPEND_IF_EXIST,
                      help="Append if existing (default: {0!s})".format((APPEND_IF_EXIST)))
    parser.add_option("-o", "--out", action="store", 
                      type="string", dest="outfile", default=CSV_OUTPUT_FILE,
                      help="CSV output file (default: {0!s})".format((CSV_OUTPUT_FILE)))
    parser.add_option("-d", "--dir", action="store", 
                      type="string", dest="outdir", default=TEXT_OUTPUT_DIR,
                      help="Text output directory (default: {0!s})".format((TEXT_OUTPUT_DIR)))
    return parser.parse_args(argv)
    
"""Data Fields Information
   Short Name | Type | Count | XPATH
   Extract from: nyt_corpus_overview.pdf
"""
DATA_FIELDS  =  [
                ('Alternate URL', 'URL', 'Single', '/nitf/head/meta[@name="alternate_url"]/@content'),
                ('Article Abstract', 'String', 'Single', '/nitf/body/body.head/abstract'),
                ('Author Biography', 'String', 'Single', '/nitf/body/body.content/block[@class="author_info"]'),
                ('Banner', 'String', 'Single', '/nitf/head/meta[@name="banner"]/@content'),
                ('Biographical Categories', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="biographical_categories"]'),
                ('Body', 'String', 'Single', '/nitf/body/body.content/block[@class="full_text"]'),
                ('Byline', 'String', 'Single', '/nitf/body/body.head/byline[@class="print_byline"]'),
                ('Column Name', 'String', 'Single', '/nitf/head/meta[@name="column_name"]/@content'),
                ('Column Number', 'Integer', 'Single', '/nitf/head/meta[@name="print_column"]/@content'),
                ('Correction Date', 'Date', 'Single', '/nitf/head/meta[@name="correction_date"]/@content'),
                ('Correction Text', 'String', 'Single', '/nitf/body/body.content/block[@class="correction_text"]'),
                ('Credit', 'String', 'Single', '/nitf/head/docdata/doc.copyright/@holder'),
                ('Dateline', 'String', 'Single', '/nitf/body/body.head/dateline'),
                ('Day Of Week', 'String', 'Single', '/nitf/head/meta[@name="publication_day_of_week"]/@content'),
                ('Descriptors', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="descriptor"]'),
                ('Feature Page', 'String', 'Single', '/nitf/head/meta[@name="feature_page"]/@content'),
                ('General Online Descriptors', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="general_descriptor"]'),
                ('Guid', 'Long', 'Single', '/nitf/head/docdata/doc-id/@id-string'),
                ('Headline', 'String', 'Single', '/nitf/body[1]/body.head/hedline/hl1'),
                ('Kicker', 'String', 'Single', '/nitf/head/docdata/series/@series.name'),
                ('Lead Paragraph', 'String', 'Single', '/nitf/body/body.content/block[@class="lead_paragraph"]'),
                ('Locations', 'String', 'Multiple', '/nitf/head/docdata/identified-content/location[@class="indexing_service"]'),
                ('Names', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="names"]'),
                ('News Desk', 'String', 'Single', '/nitf/head/meta[@name="dsk"]/@content'),
                ('Normalized Byline', 'String', 'Single', '/nitf/body/body.head/byline[@class="normalized_byline"]'),
                ('Online Descriptors', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="descriptor"]'),
                ('Online Headline', 'String', 'Single', '/nitf/body[1]/body.head/hedline/hl2'),
                ('Online Lead Paragraph', 'String', 'Single', '/nitf/body/body.content/block[@class="online_lead_paragraph"]'),
                ('Online Locations', 'String', 'Multiple', '/nitf/head/docdata/identified-content/location[@class="online_producer"]'),
                ('Online Organizations', 'String', 'Multiple', '/nitf/head/docdata/identified-content/org[@class="online_producer"]'),
                ('Online People', 'String', 'Multiple', '/nitf/head/docdata/identified-content/person[@class="online_producer"]'),
                ('Online Section', 'String', 'Single', '/nitf/head/meta[@name="online_sections"]/@content'),
                ('Online Titles', 'String', 'Multiple', '/nitf/head/docdata/identified-content/object.title[@class="online_producer"]'),
                ('Organizations', 'String', 'Multiple', '/nitf/head/docdata/identified-content/org[@class="indexing_service"]'),
                ('Page', 'Integer', 'Single', '/nitf/head/meta[@name="print_page_number"]/@content'),
                ('People', 'String', 'Multiple', '/nitf/head/docdata/identified-content/person[@class="indexing_service"]'),
                ('Publication Date', 'Date', 'Single', '/nitf/head/pubdata/@date.publication'),
                ('Publication Day Of Month', 'Integer', 'Single', '/nitf/head/meta[@name="publication_day_of_month"]/@content'),
                ('Publication Month', 'Integer', 'Single', '/nitf/head/meta[@name="publication_month"]/@content'),
                ('Publication Year', 'Integer', 'Single', '/nitf/head/meta[@name="publication_year"]/@content'),
                ('Section', 'String', 'Single', '/nitf/head/meta[@name="print_section"]/@content'),
                ('Series Name', 'String', 'Single', '/nitf/head/meta[@name="series_name"]/@content'),
                ('Slug', 'String', 'Single', '/nitf/head/meta[@name="slug"]/@content'),
                ('Taxonomic Classifiers', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="taxonomic_classifier"]'),
                ('Titles', 'String', 'Multiple', '/nitf/head/docdata/identified-content/object.title[@class="indexing_service"]'),
                ('Types Of Material', 'String', 'Multiple', '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="types_of_material"]'),
                ('Url', 'URL', 'Single', '/nitf/head/pubdata/@ex-ref'),
                ('Word Count', 'Integer', 'Single', '/nitf/head/pubdata/@item-length'),
                ]

def export_text(filename, rootdir, text):
    """Export text to file with same directory layout
    """
    try:
        relpath = os.path.relpath(filename)
    except:
        relpath = os.path.splitdrive(filename)[1]
    relpath = re.sub(r'^[\.|\\|\/]*', '', relpath)
    extdir = rootdir + '/' + os.path.dirname(relpath)
    fname = extdir + '/' + os.path.basename(relpath)
    fname = os.path.splitext(fname)[0] + '.fulltext.txt'
    print("Exporting text: {0!s}".format((fname)))
    try:
        if not os.path.exists(extdir):
            os.makedirs(extdir)
        f = open(fname, 'wt')
        f.write(text)
        f.close()
    except:
        print("ERROR")

match_by_line_re = re.compile(r'(?:By\s+)?(.*)', flags=re.I)
def reform_byline(s):
    """Returns reformatted Byline field
    """
    m = match_by_line_re.match(s)
    if m:
        return m.group(1)
    else:
        return s
    
match_people_re = re.compile(r'(.*)\s*\,\s*([^\(]*)')
def reform_people(s):
    """Returns reformatted Peoples field
    """
    peoples = s.split(MULTIVALUE_SEPARATOR)
    np = []
    for p in peoples:
        m = match_people_re.match(p)
        if m:
            np.append("{0!s} {1!s}".format(m.group(2).strip(), m.group(1).strip()))
        else:
            np.append(p)
    return MULTIVALUE_SEPARATOR.join(np)


def parse_xml(filename, xml=None, textdir=''):
    """Returns data fields parse from XML input file
    """
    print("Processing input file: {0!s}".format((filename)))
    if xml is None:
        infile = open(filename, 'rt')
        tree = etree.parse(infile)
        infile.close()
    else:
        tree = etree.fromstring(xml)
    row = []
    for f in DATA_FIELDS:
        #print f[0], f[2], f[3]
        a = tree.xpath(f[3])
        if f[2].lower() == 'single':
            if len(a):
                if type(a[0]) == etree._Element:
                    s = ' '.join(re.split('[\s\r\n\t]', etree.tostring(a[0], method='text', encoding='utf-8')))
                    s = ' '.join(s.split())
                else:
                    s = a[0]
            else:
                s = EMPTY_VALUE
        else:
            d = []
            for b in a:
                c = etree.tostring(b, method='text', encoding='utf-8').strip()
                if c != '':
                    d.append(c)
            s = MULTIVALUE_SEPARATOR.join(d)
            if s == '':
                s = EMPTY_VALUE
        if f[0].lower() == 'body':
            export_text(filename, textdir, s)
        if f[0].lower() == 'byline':
            s = reform_byline(s)
        if f[0].lower() == 'people':
            s = reform_people(s)
        row.append(s)
    return row
    
def main(options, args):
    """ Main Entry Point
    """
    rootdir = args[1]
        
    """Create output file
    """
    try:
        if options.append:
            csvfile = open(options.outfile, 'ab')
        else:
            csvfile = open(options.outfile, 'wb')        
        csvwriter = csv.writer(csvfile, dialect='excel', delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    except:
        print "ERROR: Cannot create output file"
        return -1
    if not options.append:
        h = [a[0] for a in DATA_FIELDS]
        h.append('Filename')
        csvwriter.writerow(h)
    
    # For each XML files in folder and sub-folders
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, '*.*'):
            if re.match('.*\.(tgz|xml)', filename):
                fname = os.path.join(root, filename)
                if fname.endswith('tgz'):
                    tar = tarfile.open(fname, "r:gz")
                    for tarinfo in tar:
                        fname = os.path.join(root, tarinfo.name)
                        if tarinfo.isreg():
                            f = tar.extractfile(tarinfo)
                            xml = f.read()
                            row = parse_xml(fname, xml, options.outdir)
                            row.append(fname)
                            csvwriter.writerow(row)
                    tar.close()
                else:
                    row = parse_xml(fname, None, options.outdir)
                    row.append(fname)
                    csvwriter.writerow(row)
    csvfile.close()
    return 0
    
def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    os._exit(1)
    
if __name__ == "__main__":

    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("{0!s} - r2 (2013/05/28)\n".format((os.path.basename(sys.argv[0]))))
    
    (options, args) = parse_command_line(sys.argv)

    if len(args) < 2:
        print("Please specify root directory of XML input files (-h/--help for help)")
        sys.exit(-1)
        
    main(options, args)
