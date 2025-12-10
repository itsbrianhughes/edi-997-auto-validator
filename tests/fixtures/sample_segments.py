"""Sample EDI segment strings for testing."""

# ISA Segment samples
ISA_VALID = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>"
ISA_VALID_ALT_DELIMITERS = "ISA|00|          |00|          |ZZ|SENDER         |ZZ|RECEIVER       |230101|1200|U|00401|000000001|0|P|:"

# GS Segment samples
GS_VALID = "GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010"
GS_VALID_SHORT_TIME = "GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010"

# ST Segment samples
ST_VALID = "ST*997*0001"
ST_VALID_WITH_REFERENCE = "ST*997*0001*005010"

# AK1 Segment samples
AK1_VALID = "AK1*PO*1234"
AK1_VALID_WITH_VERSION = "AK1*PO*1234*004010"

# AK2 Segment samples
AK2_VALID = "AK2*850*5678"
AK2_VALID_WITH_REFERENCE = "AK2*850*5678*005010X279A1"

# AK3 Segment samples
AK3_VALID = "AK3*N1*2"
AK3_VALID_WITH_LOOP = "AK3*N1*2*0100"
AK3_VALID_WITH_ERROR = "AK3*N1*2*0100*8"

# AK4 Segment samples
AK4_VALID = "AK4*1*66*1"
AK4_VALID_WITH_BAD_DATA = "AK4*1*66*1*INVALID_DATA"
AK4_VALID_MINIMAL = "AK4*2**7"

# AK5 Segment samples
AK5_ACCEPTED = "AK5*A"
AK5_REJECTED = "AK5*R*5"
AK5_REJECTED_MULTIPLE_ERRORS = "AK5*R*1*3*5"

# AK9 Segment samples
AK9_ACCEPTED = "AK9*A*1*1*1"
AK9_REJECTED = "AK9*R*1*0*1"
AK9_PARTIAL = "AK9*P*2*1*2"
AK9_WITH_ERRORS = "AK9*R*1*0*1*1*3"

# SE Segment samples
SE_VALID = "SE*4*0001"
SE_VALID_LARGE_COUNT = "SE*25*0001"

# GE Segment samples
GE_VALID = "GE*1*1"
GE_VALID_MULTIPLE_SETS = "GE*3*1"

# IEA Segment samples
IEA_VALID = "IEA*1*000000001"
IEA_VALID_MULTIPLE_GROUPS = "IEA*2*000000001"

# Invalid segment samples (for error testing)
INVALID_MISSING_ELEMENTS = "AK1*PO"  # Missing required group control number
INVALID_BAD_INTEGER = "AK9*A*ABC*1*1"  # Non-integer value
INVALID_EMPTY_REQUIRED = "AK1**1234"  # Empty required field

# Segments with trailing/leading whitespace
AK1_WITH_WHITESPACE = "  AK1*PO*1234  "
AK9_WITH_WHITESPACE = " AK9*A*1*1*1 "

# Complex real-world samples
REAL_WORLD_AK3 = "AK3*REF*8*2000*8"
REAL_WORLD_AK4 = "AK4*3*128*7*99"
REAL_WORLD_AK5 = "AK5*R*5*2*3"
REAL_WORLD_AK9 = "AK9*E*4*3*4*5*2"


def get_segment_sample(segment_type: str, variant: str = "valid") -> str:
    """Get a sample segment by type and variant.

    Args:
        segment_type: Segment type (ISA, GS, ST, AK1, etc.)
        variant: Variant name (valid, invalid, etc.)

    Returns:
        Sample segment string

    Raises:
        ValueError: If sample not found
    """
    samples = {
        "ISA": {
            "valid": ISA_VALID,
            "alt_delimiters": ISA_VALID_ALT_DELIMITERS,
        },
        "GS": {
            "valid": GS_VALID,
            "short_time": GS_VALID_SHORT_TIME,
        },
        "ST": {
            "valid": ST_VALID,
            "with_reference": ST_VALID_WITH_REFERENCE,
        },
        "AK1": {
            "valid": AK1_VALID,
            "with_version": AK1_VALID_WITH_VERSION,
            "with_whitespace": AK1_WITH_WHITESPACE,
            "invalid_missing": INVALID_MISSING_ELEMENTS,
        },
        "AK2": {
            "valid": AK2_VALID,
            "with_reference": AK2_VALID_WITH_REFERENCE,
        },
        "AK3": {
            "valid": AK3_VALID,
            "with_loop": AK3_VALID_WITH_LOOP,
            "with_error": AK3_VALID_WITH_ERROR,
            "real_world": REAL_WORLD_AK3,
        },
        "AK4": {
            "valid": AK4_VALID,
            "with_bad_data": AK4_VALID_WITH_BAD_DATA,
            "minimal": AK4_VALID_MINIMAL,
            "real_world": REAL_WORLD_AK4,
        },
        "AK5": {
            "accepted": AK5_ACCEPTED,
            "rejected": AK5_REJECTED,
            "multiple_errors": AK5_REJECTED_MULTIPLE_ERRORS,
            "real_world": REAL_WORLD_AK5,
        },
        "AK9": {
            "accepted": AK9_ACCEPTED,
            "rejected": AK9_REJECTED,
            "partial": AK9_PARTIAL,
            "with_errors": AK9_WITH_ERRORS,
            "with_whitespace": AK9_WITH_WHITESPACE,
            "invalid_bad_int": INVALID_BAD_INTEGER,
            "real_world": REAL_WORLD_AK9,
        },
        "SE": {
            "valid": SE_VALID,
            "large_count": SE_VALID_LARGE_COUNT,
        },
        "GE": {
            "valid": GE_VALID,
            "multiple_sets": GE_VALID_MULTIPLE_SETS,
        },
        "IEA": {
            "valid": IEA_VALID,
            "multiple_groups": IEA_VALID_MULTIPLE_GROUPS,
        },
    }

    if segment_type not in samples:
        raise ValueError(f"Unknown segment type: {segment_type}")

    if variant not in samples[segment_type]:
        raise ValueError(
            f"Unknown variant '{variant}' for segment type '{segment_type}'. "
            f"Available: {', '.join(samples[segment_type].keys())}"
        )

    return samples[segment_type][variant]


def get_all_valid_segments() -> dict[str, str]:
    """Get all valid segment samples.

    Returns:
        Dictionary mapping segment types to valid segment strings
    """
    return {
        "ISA": ISA_VALID,
        "GS": GS_VALID,
        "ST": ST_VALID,
        "AK1": AK1_VALID,
        "AK2": AK2_VALID,
        "AK3": AK3_VALID,
        "AK4": AK4_VALID,
        "AK5": AK5_ACCEPTED,
        "AK9": AK9_ACCEPTED,
        "SE": SE_VALID,
        "GE": GE_VALID,
        "IEA": IEA_VALID,
    }
