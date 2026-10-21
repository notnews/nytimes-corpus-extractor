import csv
import io
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

import nytextract

XML = """<?xml version="1.0" encoding="UTF-8"?>
<nitf><head><docdata><doc-id id-string="123"/>
<identified-content><person class="indexing_service">Doe, Jane</person>
<person class="indexing_service">Smith, John</person></identified-content>
</docdata></head><body><body.head><hedline><hl1>Café news</hl1></hedline>
<byline class="print_byline">By Jane Doe</byline></body.head>
<body.content><block class="full_text"><p>Hello café.</p><p>Next story.</p></block>
</body.content></body></nitf>""".encode()


@pytest.mark.parametrize("archive", [False, True])
def test_cli_extracts_unicode_and_metadata(tmp_path, archive):
    source = tmp_path / "input"
    source.mkdir()
    if archive:
        with tarfile.open(source / "stories.tgz", "w:gz") as handle:
            member = tarfile.TarInfo("2000/story.xml")
            member.size = len(XML)
            handle.addfile(member, io.BytesIO(XML))
    else:
        (source / "story.xml").write_bytes(XML)
    script = Path(nytextract.__file__)
    command = [sys.executable, str(script), "-o", "out.csv", "-d", "text", "input"]
    subprocess.run(command, cwd=tmp_path, check=True)
    with (tmp_path / "out.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["Guid"] == "123"
    assert rows[0]["Headline"] == "Café news"
    assert rows[0]["Byline"] == "Jane Doe"
    assert rows[0]["People"] == "Jane Doe|John Smith"
    assert rows[0]["Banner"] == "NA"
    text_files = list((tmp_path / "text").rglob("*.fulltext.txt"))
    assert len(text_files) == 1
    assert text_files[0].read_text(encoding="utf-8") == rows[0]["Body"]
    subprocess.run(command + ["--append"], cwd=tmp_path, check=True)
    with (tmp_path / "out.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_external_entity_is_not_read(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("PRIVATE_SENTINEL")
    xml = f'''<!DOCTYPE nitf [<!ENTITY xxe SYSTEM "{secret.as_uri()}">]>
    <nitf><body><body.content><block class="full_text">&xxe;</block>
    </body.content></body></nitf>'''.encode()
    row = nytextract.parse_xml("story.xml", xml, str(tmp_path / "text"))
    assert "PRIVATE_SENTINEL" not in " ".join(row)


def test_archive_cannot_write_outside_output_directory(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    with tarfile.open(source / "bad.tgz", "w:gz") as handle:
        member = tarfile.TarInfo("../escape.xml")
        member.size = len(XML)
        handle.addfile(member, io.BytesIO(XML))
    options, _ = nytextract.parse_command_line(
        ["-o", str(tmp_path / "out.csv"), "-d", str(tmp_path / "text")]
    )
    with pytest.raises(ValueError, match="Unsafe archive member"):
        nytextract.main(options, [str(source)])
    assert not (tmp_path / "escape.fulltext.txt").exists()
