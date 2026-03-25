import json
import os
import subprocess
from unittest.mock import patch

import pytest


class TestEnsureSymlinks:
    """Tests for ensure_symlinks: creates Makefile, conf.json, signature symlinks."""

    def test_creates_makefile_symlink_when_missing(self, tmp_path):
        """Makefile symlink should point to ../Makefile (relative)."""
        from lib.invoicing import ensure_symlinks

        # Setup: invoicing/Makefile exists, invoicing/season/ is our target dir
        invoicing_dir = tmp_path / "invoicing"
        invoicing_dir.mkdir()
        (invoicing_dir / "Makefile").write_text("# makefile")
        season_dir = invoicing_dir / "season"
        season_dir.mkdir()

        config = {"conf": {}}

        ensure_symlinks(str(season_dir), config)

        link = season_dir / "Makefile"
        assert link.is_symlink()
        assert os.readlink(str(link)) == "../Makefile"

    def test_creates_conf_json_symlink(self, tmp_path):
        """conf.json symlink should point to the config file path (absolute)."""
        from lib.invoicing import ensure_symlinks

        invoicing_dir = tmp_path / "invoicing"
        invoicing_dir.mkdir()
        (invoicing_dir / "Makefile").write_text("# makefile")
        season_dir = invoicing_dir / "season"
        season_dir.mkdir()

        conf_path = tmp_path / "conf.json"
        conf_path.write_text('{"test": true}')

        config = {"conf": {"dir": str(tmp_path)}}

        ensure_symlinks(str(season_dir), config)

        link = season_dir / "conf.json"
        assert link.is_symlink()
        assert os.readlink(str(link)) == str(conf_path)

    def test_does_nothing_when_symlinks_already_exist(self, tmp_path):
        """Calling ensure_symlinks twice should not raise or change links."""
        from lib.invoicing import ensure_symlinks

        invoicing_dir = tmp_path / "invoicing"
        invoicing_dir.mkdir()
        (invoicing_dir / "Makefile").write_text("# makefile")
        (invoicing_dir / "signature.png").write_bytes(b"PNG")
        season_dir = invoicing_dir / "season"
        season_dir.mkdir()

        conf_path = tmp_path / "conf.json"
        conf_path.write_text('{"test": true}')

        config = {"conf": {"dir": str(tmp_path)}}

        ensure_symlinks(str(season_dir), config)
        # Second call should be a no-op
        ensure_symlinks(str(season_dir), config)

        assert (season_dir / "Makefile").is_symlink()
        assert (season_dir / "conf.json").is_symlink()
        assert (season_dir / "signature.png").is_symlink()


class TestFindMemberFile:
    """Tests for find_member_file: scan JSON files to find by item id."""

    def test_finds_correct_file_by_item_id(self, tmp_path):
        """Should return filepath of JSON file containing matching id."""
        from lib.invoicing import find_member_file

        member_data = {"id": 12345, "name": "Test Member"}
        filepath = tmp_path / "john_doe_2024-01-01_12345.json"
        filepath.write_text(json.dumps(member_data))

        # Also create a non-matching file
        other_data = {"id": 99999, "name": "Other Member"}
        other_path = tmp_path / "jane_doe_2024-02-01_99999.json"
        other_path.write_text(json.dumps(other_data))

        result = find_member_file(str(tmp_path), 12345)
        assert result == str(filepath)

    def test_returns_none_for_unknown_id(self, tmp_path):
        """Should return None when no JSON file matches the id."""
        from lib.invoicing import find_member_file

        member_data = {"id": 12345, "name": "Test Member"}
        filepath = tmp_path / "john_doe_2024-01-01_12345.json"
        filepath.write_text(json.dumps(member_data))

        result = find_member_file(str(tmp_path), 77777)
        assert result is None

    def test_skips_conf_json(self, tmp_path):
        """Should not read conf.json even if it contains an id field."""
        from lib.invoicing import find_member_file

        conf_data = {"id": 12345, "credentials": {}}
        (tmp_path / "conf.json").write_text(json.dumps(conf_data))

        result = find_member_file(str(tmp_path), 12345)
        assert result is None


class TestRunMakePdf:
    """Tests for run_make_pdf: subprocess wrapper for make <file>.pdf."""

    @patch("lib.invoicing.subprocess.run")
    def test_calls_subprocess_with_correct_args(self, mock_run, tmp_path):
        """Should call make with the json basename + .pdf in the invoicing dir."""
        from lib.invoicing import run_make_pdf

        mock_run.return_value = subprocess.CompletedProcess(
            args=["make", "foo.pdf"], returncode=0, stdout="", stderr=""
        )

        result = run_make_pdf(str(tmp_path), "foo")

        mock_run.assert_called_once_with(
            ["make", "foo.pdf"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.returncode == 0

    @patch("lib.invoicing.subprocess.run")
    def test_raises_on_failure(self, mock_run):
        """Should propagate CalledProcessError when make fails."""
        from lib.invoicing import run_make_pdf

        mock_run.side_effect = subprocess.CalledProcessError(
            2, "make", output="", stderr="error"
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_make_pdf("/tmp", "broken")


class TestRunMakeEmail:
    """Tests for run_make_email: subprocess wrapper for make <file>.mail.log."""

    @patch("lib.invoicing.subprocess.run")
    def test_calls_subprocess_with_correct_args(self, mock_run, tmp_path):
        """Should call make with the json basename + .mail.log."""
        from lib.invoicing import run_make_email

        mock_run.return_value = subprocess.CompletedProcess(
            args=["make", "foo.mail.log"], returncode=0, stdout="", stderr=""
        )

        result = run_make_email(str(tmp_path), "foo")

        mock_run.assert_called_once_with(
            ["make", "foo.mail.log"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.returncode == 0


class TestRenderInvoiceHtml:
    """Tests for render_invoice_html: Jinja2 template rendering."""

    def test_returns_html_with_member_data(self, tmp_path, sample_helloasso_item):
        """Rendered HTML should contain member name and invoice number."""
        from lib.invoicing import render_invoice_html

        # Use the real template
        import shutil
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        shutil.copy(
            "/home/user/acs_helloasso_invoicing/invoicing/template.jinja2",
            str(template_dir / "template.jinja2"),
        )
        # Also copy style.css so template link doesn't break rendering
        style_src = "/home/user/acs_helloasso_invoicing/invoicing/style.css"
        if os.path.isfile(style_src):
            shutil.copy(style_src, str(template_dir / "style.css"))

        # The real template expects opt["amount"] on options
        item = dict(sample_helloasso_item)
        item["options"] = [
            {"name": "Football", "amount": 5000},
            {"name": "Tennis", "amount": 3000},
            {"name": "N'oubliez pas de venir", "amount": 0},
        ]

        html = render_invoice_html(str(template_dir), item)

        assert "Jean-Pierre" in html
        assert "De La Fontaine" in html
        assert "12345" in html
        assert "Facture" in html

    def test_injects_today_date(self, tmp_path, sample_helloasso_item):
        """Rendered HTML should contain today's date in dd/mm/YYYY format."""
        from lib.invoicing import render_invoice_html
        from datetime import date

        # Use a minimal template that just outputs {{ date }}
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "template.jinja2").write_text(
            "<html>Date: {{ date }}</html>"
        )

        html = render_invoice_html(str(template_dir), sample_helloasso_item)

        today = date.today().strftime("%d/%m/%Y")
        assert today in html

    def test_injects_signature_path(self, tmp_path, sample_helloasso_item):
        """Rendered HTML should contain the signature path when provided."""
        from lib.invoicing import render_invoice_html

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "template.jinja2").write_text(
            "<html>Sig: {{ signature }}</html>"
        )

        html = render_invoice_html(
            str(template_dir), sample_helloasso_item,
            signature_path="/path/to/sig.png"
        )

        assert "/path/to/sig.png" in html

    def test_signature_defaults_to_empty(self, tmp_path, sample_helloasso_item):
        """Without signature_path, signature variable should be empty string."""
        from lib.invoicing import render_invoice_html

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "template.jinja2").write_text(
            "<html>Sig:[{{ signature }}]</html>"
        )

        html = render_invoice_html(str(template_dir), sample_helloasso_item)

        assert "Sig:[]" in html
