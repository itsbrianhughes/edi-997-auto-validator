"""Sample 997 EDI files for testing."""

# Sample 997 with accepted transaction (standard delimiters: *, ~, >)
SAMPLE_997_ACCEPTED = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*997*0001~AK1*PO*1234~AK9*A*1*1*1~SE*4*0001~GE*1*1~IEA*1*000000001~"""

# Sample 997 with rejected transaction
SAMPLE_997_REJECTED = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*997*0001~AK1*PO*1234~AK2*850*5678~AK3*N1*2~AK4*1*66*1*1~AK5*R*5~AK9*R*1*0*1~SE*8*0001~GE*1*1~IEA*1*000000001~"""

# Sample 997 with line breaks (same as accepted but formatted)
SAMPLE_997_WITH_LINE_BREAKS = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~
GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~
ST*997*0001~
AK1*PO*1234~
AK9*A*1*1*1~
SE*4*0001~
GE*1*1~
IEA*1*000000001~
"""

# Sample 997 with alternative delimiters (pipe, exclamation, colon)
SAMPLE_997_ALT_DELIMITERS = """ISA|00|          |00|          |ZZ|SENDER         |ZZ|RECEIVER       |230101|1200|U|00401|000000001|0|P|:!GS|FA|SENDER|RECEIVER|20230101|1200|1|X|004010!ST|997|0001!AK1|PO|1234!AK9|A|1|1|1!SE|4|0001!GE|1|1!IEA|1|000000001!"""

# Sample 997 with partial acceptance
SAMPLE_997_PARTIAL = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*997*0001~AK1*PO*1234~AK2*850*5678~AK5*E*5~AK9*E*1*1*1~SE*6*0001~GE*1*1~IEA*1*000000001~"""

# Multiple functional groups in one interchange
SAMPLE_997_MULTIPLE_GROUPS = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*997*0001~AK1*PO*1234~AK9*A*1*1*1~SE*4*0001~GE*1*1~GS*FA*SENDER*RECEIVER*20230101*1201*2*X*004010~ST*997*0002~AK1*SH*5678~AK9*A*1*1*1~SE*4*0002~GE*1*2~IEA*2*000000001~"""

# Minimal valid ISA segment (for delimiter detection testing)
MINIMAL_ISA = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~"""

# Invalid ISA - too short
INVALID_ISA_TOO_SHORT = """ISA*00*TEST~"""

# Invalid ISA - doesn't start with ISA
INVALID_NO_ISA = """GSA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~"""

# Empty content
EMPTY_CONTENT = ""

# Only whitespace
WHITESPACE_ONLY = "   \n  \t  \n  "

# Large EDI file (simulated with repeated segments)
LARGE_EDI_SAMPLE = (
    """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~"""
    + """GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~"""
    + """ST*997*0001~"""
    + ("""AK2*850*{}~AK5*A*5~""" * 100).format(*range(100))
    + """AK9*A*1*1*1~SE*204*0001~GE*1*1~IEA*1*000000001~"""
)

# EDI with Windows line endings (CRLF)
SAMPLE_997_CRLF = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~\r\nGS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~\r\nST*997*0001~\r\nAK1*PO*1234~\r\nAK9*A*1*1*1~\r\nSE*4*0001~\r\nGE*1*1~\r\nIEA*1*000000001~\r\n"""

# EDI with mixed line endings
SAMPLE_997_MIXED_ENDINGS = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~\nGS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~\r\nST*997*0001~\rAK1*PO*1234~\nAK9*A*1*1*1~\r\nSE*4*0001~\nGE*1*1~\r\nIEA*1*000000001~"""


def get_sample_by_name(name: str) -> str:
    """Get a sample EDI file by name.

    Args:
        name: Sample name (e.g., 'accepted', 'rejected', 'partial')

    Returns:
        Sample EDI content

    Raises:
        ValueError: If sample name not found
    """
    samples = {
        "accepted": SAMPLE_997_ACCEPTED,
        "rejected": SAMPLE_997_REJECTED,
        "partial": SAMPLE_997_PARTIAL,
        "with_line_breaks": SAMPLE_997_WITH_LINE_BREAKS,
        "alt_delimiters": SAMPLE_997_ALT_DELIMITERS,
        "multiple_groups": SAMPLE_997_MULTIPLE_GROUPS,
        "minimal_isa": MINIMAL_ISA,
        "invalid_short": INVALID_ISA_TOO_SHORT,
        "invalid_no_isa": INVALID_NO_ISA,
        "empty": EMPTY_CONTENT,
        "whitespace": WHITESPACE_ONLY,
        "large": LARGE_EDI_SAMPLE,
        "crlf": SAMPLE_997_CRLF,
        "mixed_endings": SAMPLE_997_MIXED_ENDINGS,
    }

    if name not in samples:
        raise ValueError(
            f"Unknown sample name: {name}. Available: {', '.join(samples.keys())}"
        )

    return samples[name]


def get_all_sample_names() -> list:
    """Get list of all available sample names.

    Returns:
        List of sample names
    """
    return [
        "accepted",
        "rejected",
        "partial",
        "with_line_breaks",
        "alt_delimiters",
        "multiple_groups",
        "minimal_isa",
        "invalid_short",
        "invalid_no_isa",
        "empty",
        "whitespace",
        "large",
        "crlf",
        "mixed_endings",
    ]
