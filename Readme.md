### NY Times Corpus Extractor

The NY Times Corpus at: [https://catalog.ldc.upenn.edu/LDC2008T19](https://catalog.ldc.upenn.edu/LDC2008T19).

Unzip the NY Times Corpus and then run the script. Script produces a csv and files containing text of stories.

#### Requirements
[lxml 3.1.1](https://pypi.python.org/pypi/lxml/3.1.1)

#### Instructions

<pre><code>
Usage: nytextract.py [options] <xml directory>

Options:
  -h, --help            show this help message and exit
  -a, --append          Append if existing (default: False)
  -o OUTFILE, --out=OUTFILE
                        CSV output file (default: outfile.csv)
  -d OUTDIR, --dir=OUTDIR
                        Text output directory (default: text)

</code></pre>

#### USAGE EXAMPLE:
<pre><code>
    python nytextract.py -o 2000.csv -d text 2000
</code></pre>    

This command will be process all XML file in folder 2000 and generate CSV output file "2000.csv".  
The output text files store in folder "text"

#### License
Scripts are released under the [MIT License](https://github.com/soodoku/NY_Times_Corpus_Extractor/blob/master/License.md).
