"""Test that a malformed row in the Actions table doesn't drop the actions
listed after it.

AWS lists actions alphabetically. A single row without the expected six columns
(a "Scenario" sub-row, or a structural change like newly inserted actions) used
to abort parsing of the whole table, silently dropping that action and every
action after it. That is how `acm:RequestCertificate` vanished once AWS added
new ACME actions above it.
"""

import json
from pathlib import Path

import aws_iam_db.docs as docs

# A minimal service page shaped like AWS's. "MiddleScenario" is a malformed row
# (only 1 cell) sitting between two real actions; the alphabetically-later
# "ZzzLastAction" must still be parsed.
SYNTH_PAGE = """
<html><body>
<div id="main-content">
  <h1 class="topictitle">Actions, resources, and condition keys for Test Service</h1>
  <p>The prefix is <code class="code">test</code>.</p>
  <div class="table-contents">
    <table>
      <tr>
        <th>Actions</th><th>Description</th><th>Access level</th>
        <th>Resource types</th><th>Condition keys</th><th>Dependent actions</th>
      </tr>
      <tr>
        <td><a href="#a">AaaFirstAction</a></td><td>first</td><td>Read</td>
        <td></td><td></td><td></td>
      </tr>
      <tr>
        <td colspan="2">MiddleScenario (malformed, not six cells)</td>
      </tr>
      <tr>
        <td><a href="#z">ZzzLastAction</a></td><td>last</td><td>Write</td>
        <td></td><td></td><td></td>
      </tr>
    </table>
  </div>
</div>
</body></html>
"""


def _parse(tmp_path, monkeypatch):
    docs_dir = Path("/tmp/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    for existing in docs_dir.iterdir():
        existing.unlink()
    (docs_dir / "list_testservice.html").write_text(SYNTH_PAGE)

    # Don't hit the network; parse the file we just wrote.
    monkeypatch.setattr(docs, "update_html_docs_directory", lambda dest: None)

    out = tmp_path / "out.json"
    docs.get_docs(str(out))
    data = json.loads(out.read_text())
    return next(s for s in data if s["prefix"] == "test")


def test_malformed_row_does_not_drop_following_actions(tmp_path, monkeypatch):
    service = _parse(tmp_path, monkeypatch)
    names = [p["privilege"] for p in service["privileges"]]
    assert "AaaFirstAction" in names
    # The action after the malformed row is the regression guard: the old
    # `break` dropped it.
    assert "ZzzLastAction" in names
