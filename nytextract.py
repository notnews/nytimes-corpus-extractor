#!/usr/bin/env python

import csv
import logging
import optparse
import re
import signal
import sys
import tarfile
from pathlib import Path

from lxml import etree

# ===========================================================================================================
# Default configuration
CSV_OUTPUT_FILE = "outfile.csv"  # Default CSV output file
TEXT_OUTPUT_DIR = "text"  # Default Text files output directory
MULTIVALUE_SEPARATOR = "|"  # Multiple value field separator
EMPTY_VALUE = "NA"  # Empty field value

APPEND_IF_EXIST = False  # True or False
# ===========================================================================================================

logger = logging.getLogger("nytextract")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

usage = "Usage: %prog [options] <xml directory>"


def parse_command_line(argv):
    """Command line options parser"""

    parser = optparse.OptionParser(add_help_option=True, usage=usage)

    parser.add_option(
        "-a",
        "--append",
        action="store_true",
        dest="append",
        default=APPEND_IF_EXIST,
        help=f"Append if existing (default: {APPEND_IF_EXIST!s})",
    )
    parser.add_option(
        "-o",
        "--out",
        action="store",
        type="string",
        dest="outfile",
        default=CSV_OUTPUT_FILE,
        help=f"CSV output file (default: {CSV_OUTPUT_FILE!s})",
    )
    parser.add_option(
        "-d",
        "--dir",
        action="store",
        type="string",
        dest="outdir",
        default=TEXT_OUTPUT_DIR,
        help=f"Text output directory (default: {TEXT_OUTPUT_DIR!s})",
    )
    return parser.parse_args(argv)


"""Data Fields Information
   Short Name | Type | Count | XPATH
   Extract from: nyt_corpus_overview.pdf
"""
DATA_FIELDS = [
    (
        "Alternate URL",
        "URL",
        "Single",
        '/nitf/head/meta[@name="alternate_url"]/@content',
    ),
    ("Article Abstract", "String", "Single", "/nitf/body/body.head/abstract"),
    (
        "Author Biography",
        "String",
        "Single",
        '/nitf/body/body.content/block[@class="author_info"]',
    ),
    ("Banner", "String", "Single", '/nitf/head/meta[@name="banner"]/@content'),
    (
        "Biographical Categories",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="biographical_categories"]',
    ),
    ("Body", "String", "Single", '/nitf/body/body.content/block[@class="full_text"]'),
    (
        "Byline",
        "String",
        "Single",
        '/nitf/body/body.head/byline[@class="print_byline"]',
    ),
    (
        "Column Name",
        "String",
        "Single",
        '/nitf/head/meta[@name="column_name"]/@content',
    ),
    (
        "Column Number",
        "Integer",
        "Single",
        '/nitf/head/meta[@name="print_column"]/@content',
    ),
    (
        "Correction Date",
        "Date",
        "Single",
        '/nitf/head/meta[@name="correction_date"]/@content',
    ),
    (
        "Correction Text",
        "String",
        "Single",
        '/nitf/body/body.content/block[@class="correction_text"]',
    ),
    ("Credit", "String", "Single", "/nitf/head/docdata/doc.copyright/@holder"),
    ("Dateline", "String", "Single", "/nitf/body/body.head/dateline"),
    (
        "Day Of Week",
        "String",
        "Single",
        '/nitf/head/meta[@name="publication_day_of_week"]/@content',
    ),
    (
        "Descriptors",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="descriptor"]',
    ),
    (
        "Feature Page",
        "String",
        "Single",
        '/nitf/head/meta[@name="feature_page"]/@content',
    ),
    (
        "General Online Descriptors",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="general_descriptor"]',
    ),
    ("Guid", "Long", "Single", "/nitf/head/docdata/doc-id/@id-string"),
    ("Headline", "String", "Single", "/nitf/body[1]/body.head/hedline/hl1"),
    ("Kicker", "String", "Single", "/nitf/head/docdata/series/@series.name"),
    (
        "Lead Paragraph",
        "String",
        "Single",
        '/nitf/body/body.content/block[@class="lead_paragraph"]',
    ),
    (
        "Locations",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/location[@class="indexing_service"]',
    ),
    (
        "Names",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="indexing_service" and @type="names"]',
    ),
    ("News Desk", "String", "Single", '/nitf/head/meta[@name="dsk"]/@content'),
    (
        "Normalized Byline",
        "String",
        "Single",
        '/nitf/body/body.head/byline[@class="normalized_byline"]',
    ),
    (
        "Online Descriptors",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="descriptor"]',
    ),
    ("Online Headline", "String", "Single", "/nitf/body[1]/body.head/hedline/hl2"),
    (
        "Online Lead Paragraph",
        "String",
        "Single",
        '/nitf/body/body.content/block[@class="online_lead_paragraph"]',
    ),
    (
        "Online Locations",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/location[@class="online_producer"]',
    ),
    (
        "Online Organizations",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/org[@class="online_producer"]',
    ),
    (
        "Online People",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/person[@class="online_producer"]',
    ),
    (
        "Online Section",
        "String",
        "Single",
        '/nitf/head/meta[@name="online_sections"]/@content',
    ),
    (
        "Online Titles",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/object.title[@class="online_producer"]',
    ),
    (
        "Organizations",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/org[@class="indexing_service"]',
    ),
    (
        "Page",
        "Integer",
        "Single",
        '/nitf/head/meta[@name="print_page_number"]/@content',
    ),
    (
        "People",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/person[@class="indexing_service"]',
    ),
    ("Publication Date", "Date", "Single", "/nitf/head/pubdata/@date.publication"),
    (
        "Publication Day Of Month",
        "Integer",
        "Single",
        '/nitf/head/meta[@name="publication_day_of_month"]/@content',
    ),
    (
        "Publication Month",
        "Integer",
        "Single",
        '/nitf/head/meta[@name="publication_month"]/@content',
    ),
    (
        "Publication Year",
        "Integer",
        "Single",
        '/nitf/head/meta[@name="publication_year"]/@content',
    ),
    ("Section", "String", "Single", '/nitf/head/meta[@name="print_section"]/@content'),
    (
        "Series Name",
        "String",
        "Single",
        '/nitf/head/meta[@name="series_name"]/@content',
    ),
    ("Slug", "String", "Single", '/nitf/head/meta[@name="slug"]/@content'),
    (
        "Taxonomic Classifiers",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="taxonomic_classifier"]',
    ),
    (
        "Titles",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/object.title[@class="indexing_service"]',
    ),
    (
        "Types Of Material",
        "String",
        "Multiple",
        '/nitf/head/docdata/identified-content/classifier[@class="online_producer" and @type="types_of_material"]',
    ),
    ("Url", "URL", "Single", "/nitf/head/pubdata/@ex-ref"),
    ("Word Count", "Integer", "Single", "/nitf/head/pubdata/@item-length"),
]


def export_text(filename, rootdir, text):
    """Export text beneath rootdir, retaining the input directory layout."""
    parts = Path(filename).parts
    if ".." in parts:
        raise ValueError("Input paths must not contain parent-directory traversal")
    relative = Path(
        *[part for part in parts if part not in (Path(filename).anchor, ".")]
    )
    target = (Path(rootdir) / relative).with_suffix(".fulltext.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


match_by_line_re = re.compile(r"(?:By\s+)?(.*)", flags=re.IGNORECASE)


def reform_byline(s):
    """Returns reformatted Byline field"""
    m = match_by_line_re.match(s)
    if m:
        return m.group(1)
    else:
        return s


match_people_re = re.compile(r"(.*)\s*\,\s*([^\(]*)")


def reform_people(s):
    """Returns reformatted Peoples field"""
    peoples = s.split(MULTIVALUE_SEPARATOR)
    np = []
    for p in peoples:
        m = match_people_re.match(p)
        if m:
            np.append(f"{m.group(2).strip()!s} {m.group(1).strip()!s}")
        else:
            np.append(p)
    return MULTIVALUE_SEPARATOR.join(np)


def parse_xml(filename, xml=None, textdir=""):
    """Returns data fields parse from XML input file"""
    print(f"Processing input file: {filename!s}")
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    if xml is None:
        tree = etree.parse(str(filename), parser)
    else:
        tree = etree.fromstring(xml, parser)
    row = []
    for f in DATA_FIELDS:
        # print f[0], f[2], f[3]
        a = tree.xpath(f[3])
        if f[2].lower() == "single":
            if len(a):
                if isinstance(a[0], etree._Element):
                    s = " ".join(
                        re.split(
                            r"[\s\r\n\t]",
                            etree.tostring(a[0], method="text", encoding="unicode"),
                        )
                    )
                    s = " ".join(s.split())
                else:
                    s = a[0]
            else:
                s = EMPTY_VALUE
        else:
            d = []
            for b in a:
                c = etree.tostring(b, method="text", encoding="unicode").strip()
                if c != "":
                    d.append(c)
            s = MULTIVALUE_SEPARATOR.join(d)
            if s == "":
                s = EMPTY_VALUE
        if f[0].lower() == "body":
            export_text(filename, textdir, s)
        if f[0].lower() == "byline":
            s = reform_byline(s)
        if f[0].lower() == "people":
            s = reform_people(s)
        row.append(s)
    return row


def main(options, args):
    """Extract XML files and XML members of gzip-compressed tar archives."""
    rootdir = Path(args[0])
    if not rootdir.is_dir():
        raise ValueError(f"Input directory does not exist: {rootdir}")
    mode = "a" if options.append else "w"
    with open(options.outfile, mode, encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not options.append:
            writer.writerow([field[0] for field in DATA_FIELDS] + ["Filename"])
        for path in sorted(rootdir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix == ".xml":
                writer.writerow(
                    parse_xml(str(path), textdir=options.outdir) + [str(path)]
                )
            elif path.suffix == ".tgz":
                with tarfile.open(path, "r:gz") as archive:
                    for member in archive:
                        if not member.isfile() or not member.name.endswith(".xml"):
                            continue
                        member_path = Path(member.name)
                        if member_path.is_absolute() or ".." in member_path.parts:
                            raise ValueError(f"Unsafe archive member: {member.name}")
                        filename = str(path.parent / member_path)
                        with archive.extractfile(member) as source:
                            row = parse_xml(filename, source.read(), options.outdir)
                        writer.writerow(row + [filename])
    return 0


def signal_handler(signum, frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    options, args = parse_command_line(sys.argv[1:])
    if len(args) != 1:
        print(
            "Specify one directory of XML input files (-h/--help for help)",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(main(options, args))
