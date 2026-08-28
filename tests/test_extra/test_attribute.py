"""Test attribute selectors."""
import subprocess
import sys
from .. import util

# Catastrophic backtracking cannot be interrupted from within the process: `re` holds the
# GIL while matching and `signal.alarm` does not exist on Windows. So selectors that used
# to hang the regex engine are compiled in a child process which can be killed on timeout.
COMPILE_TIMEOUT = 10
COMPILE_SCRIPT = """
import sys
import soupsieve as sv

try:
    sv.compile(sys.stdin.read())
except sv.SelectorSyntaxError:
    sys.exit(0)
sys.exit(3)
"""


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_fast_syntax_error(self, selector):
        """Assert a bad selector fails for a syntax error, not a timeout error."""

        try:
            status = subprocess.run(
                [sys.executable, '-c', COMPILE_SCRIPT],
                input=selector.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=COMPILE_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            self.fail(
                'Compiling {!r} (length {}) did not complete in {} seconds'.format(
                    selector[:20] + '...', len(selector), COMPILE_TIMEOUT
                )
            )
        self.assertEqual(
            status.returncode,
            0,
            'Expected a syntax error, got exit code {}\n{}'.format(
                status.returncode, status.stderr.decode('utf-8', 'replace')
            )
        )

    def test_bad_attribute_unclosed_double_quote(self):
        """Test bad attribute with an unclosed double quoted value fails for syntax error, not timeout error."""

        self.assert_fast_syntax_error('[a="' + ('x' * 300))

    def test_bad_attribute_unclosed_single_quote(self):
        """Test bad attribute with an unclosed single quoted value fails for syntax error, not timeout error."""

        self.assert_fast_syntax_error("[a='" + ('x' * 300))

    def test_bad_attribute_unclosed_bracket(self):
        """Test bad attribute with an unquoted value and no closing bracket fails for syntax error, not timeout."""

        self.assert_fast_syntax_error('[a=' + ('x' * 300))

    def test_bad_contains_unclosed_quote(self):
        """Test bad `:-soup-contains` with an unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_fast_syntax_error(':-soup-contains("' + ('x' * 300))

    def test_bad_lang_unclosed_quote(self):
        """Test bad `:lang` with an unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_fast_syntax_error(':lang("' + ('x' * 300))
