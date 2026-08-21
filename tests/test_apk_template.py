"""Guards for the embedded WebView Activity source in apk_builder.

The Java template ships as a string (ACTIVITY_JAVA) and is compiled on the
build host, far away from CI — so these tests assert the load-bearing pieces
of the source stay intact rather than executing anything.
"""

from server.engine.apk_builder import ACTIVITY_JAVA, ApkBuilder


def test_activity_java_braces_balanced():
    # Catches truncated / badly merged template edits before they reach the
    # build host and fail there with a cryptic javac error.
    assert ACTIVITY_JAVA.count("{") == ACTIVITY_JAVA.count("}")


def test_file_chooser_is_wired_end_to_end():
    # Issue #16: <input type="file"> did nothing because AppChromeClient never
    # overrode onShowFileChooser (WebView has no default picker).
    assert "@Override public boolean onShowFileChooser(" in ACTIVITY_JAVA
    assert "startActivityForResult(intent, REQ_FILE_CHOOSER)" in ACTIVITY_JAVA
    assert "protected void onActivityResult" in ACTIVITY_JAVA
    assert "if (requestCode != REQ_FILE_CHOOSER) return;" in ACTIVITY_JAVA
    assert "callback.onReceiveValue(parseFileChooserResult(resultCode, data))" in ACTIVITY_JAVA
    assert "private Uri[] parseFileChooserResult(int resultCode, Intent data)" in ACTIVITY_JAVA


def test_file_chooser_callback_always_settled():
    # A callback that is never answered makes WebView silently drop every
    # later <input type="file"> tap, so both the stale-chooser path and the
    # cancel path must deliver null.
    assert ACTIVITY_JAVA.count("pendingFileChoiceCallback.onReceiveValue(null)") == 1
    assert "callback.onReceiveValue(parseFileChooserResult(resultCode, data))" in ACTIVITY_JAVA


def test_file_chooser_imports_present():
    assert "import android.content.ClipData;" in ACTIVITY_JAVA
    assert "import android.webkit.ValueCallback;" in ACTIVITY_JAVA


def test_template_revision_is_bumped_slug():
    # Any change to ACTIVITY_JAVA must come with a new TEMPLATE_REVISION or
    # build hosts keep serving the cached (stale) template APK.
    revision = ApkBuilder.TEMPLATE_REVISION
    parts = revision.split("-")
    assert len(parts) >= 4
    assert all(part.isdigit() for part in parts[:3])  # YYYY-MM-DD prefix
    assert parts[3]  # feature slug
