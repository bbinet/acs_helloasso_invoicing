import os
import json

from lib.filesystem import get_invoicing_dir, get_member_filepath, dump_item, scan_members, get_member_status


def test_get_invoicing_dir(sample_config, tmp_path):
    conf = sample_config["conf"]
    conf["dir"] = str(tmp_path)
    result = get_invoicing_dir(conf)
    expected = os.path.join(str(tmp_path), "invoicing", "adhesion-2024-2025")
    assert result == expected


def test_get_member_filepath(sample_config, sample_helloasso_item, tmp_path):
    conf = sample_config["conf"]
    conf["dir"] = str(tmp_path)
    result = get_member_filepath(conf, sample_helloasso_item)
    expected = os.path.join(str(tmp_path), "invoicing", "adhesion-2024-2025",
                            "jean-pierre_delafontaine_2024-09-15_12345.json")
    assert result == expected


def test_dump_item(tmp_path, sample_helloasso_item):
    filepath = os.path.join(str(tmp_path), "test_item.json")
    dump_item(filepath, sample_helloasso_item)
    assert os.path.isfile(filepath)
    with open(filepath) as f:
        loaded = json.load(f)
    assert loaded["id"] == 12345


def test_scan_members(tmp_path):
    # Create some member JSON files and a conf.json that should be excluded
    for name in ["alice_smith_2024-01-01_1.json", "bob_jones_2024-01-02_2.json", "conf.json"]:
        (tmp_path / name).write_text(json.dumps({"name": name}))
    result = scan_members(str(tmp_path))
    filenames = [os.path.basename(p) for p in result]
    assert "conf.json" not in filenames
    assert len(filenames) == 2
    assert "alice_smith_2024-01-01_1.json" in filenames
    assert "bob_jones_2024-01-02_2.json" in filenames


def test_get_member_status_both_false(tmp_path):
    filepath = tmp_path / "member_123.json"
    filepath.write_text("{}")
    status = get_member_status(str(filepath))
    assert status["invoice_generated"] is False
    assert status["email_sent"] is False


def test_get_member_status_pdf_exists(tmp_path):
    filepath = tmp_path / "member_123.json"
    filepath.write_text("{}")
    (tmp_path / "member_123.pdf").write_text("")
    status = get_member_status(str(filepath))
    assert status["invoice_generated"] is True
    assert status["email_sent"] is False


def test_get_member_status_mail_log_exists(tmp_path):
    filepath = tmp_path / "member_123.json"
    filepath.write_text("{}")
    (tmp_path / "member_123.mail.log").write_text("")
    status = get_member_status(str(filepath))
    assert status["invoice_generated"] is False
    assert status["email_sent"] is True
