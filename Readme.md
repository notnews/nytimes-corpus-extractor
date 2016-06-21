### Extract All the Fields from the New York Times Corpus to a CSV

[![Code Issues](https://www.quantifiedcode.com/api/v1/project/2d691a58502042249fdfa7c1a8bf24b2/badge.svg)](https://www.quantifiedcode.com/app/project/2d691a58502042249fdfa7c1a8bf24b2)

The New York Times Corpus is a collection of 1.8 million articles published between 1987 and 2007 along with a fair bit of meta data. For more details about The NY Times Corpus, see [https://catalog.ldc.upenn.edu/LDC2008T19](https://catalog.ldc.upenn.edu/LDC2008T19).

Once you have the NY Times Corpus, unzip it to a folder. And then run the script. Script produces a csv and text files containing story text.

#### Installation

To install the dependency [lxml 3.1.1](https://pypi.python.org/pypi/lxml/3.1.1):

```
pip install -r requirements.txt
```

#### Usage

```
python nytextract.py [options] <xml directory>
```

**Options:**

```

  -h, --help            show this help message and exit
  -a, --append          Append if existing (default: False)
  -o OUTFILE, --out=OUTFILE
                        CSV output file (default: outfile.csv)
  -d OUTDIR, --dir=OUTDIR
                        Text output directory (default: text)
```

**Example**
To process all XML files in the folder 2000 (carrying files from year 2000):  

```
python nytextract.py -o 2000.csv -d text 2000
```

The script will generate a CSV "2000.csv". Story text files will be stored in a folder "text." This folder will have the exact same structure as the folder '2000.'

#### License
Scripts are released under the [MIT License](https://opensource.org/licenses/MIT).
