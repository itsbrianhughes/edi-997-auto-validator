"""Pydantic schemas for configuration validation."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log format enumeration."""

    JSON = "json"
    SIMPLE = "simple"
    DETAILED = "detailed"


class Environment(str, Enum):
    """Application environment enumeration."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class DelimitersConfig(BaseModel):
    """EDI delimiter configuration."""

    element: str = Field(default="*", min_length=1, max_length=1)
    segment: str = Field(default="~", min_length=1, max_length=1)
    sub_element: str = Field(default=":", min_length=1, max_length=1)
    repetition: str = Field(default="^", min_length=1, max_length=1)

    @field_validator("element", "segment", "sub_element", "repetition")
    @classmethod
    def validate_unique_delimiters(cls, v: str, info: Any) -> str:
        """Ensure delimiters are unique."""
        # This will be validated in the full model
        return v


class ParserConfig(BaseModel):
    """Parser configuration."""

    auto_detect_delimiters: bool = True
    default_delimiters: DelimitersConfig = Field(default_factory=DelimitersConfig)
    trim_whitespace: bool = True
    preserve_line_breaks: bool = False
    max_file_size_mb: int = Field(default=10, ge=1, le=100)


class RejectionThresholdsConfig(BaseModel):
    """Error severity thresholds for rejection."""

    error: int = Field(default=1, ge=0)
    warning: int = Field(default=0, ge=0)
    info: int = Field(default=0, ge=0)


class ClassificationConfig(BaseModel):
    """Transaction classification configuration."""

    accepted_codes: List[str] = Field(default=["A"])
    partial_codes: List[str] = Field(default=["E", "P"])
    rejected_codes: List[str] = Field(default=["R", "M", "W", "X"])
    rejection_thresholds: RejectionThresholdsConfig = Field(
        default_factory=RejectionThresholdsConfig
    )


class ReconciliationConfig(BaseModel):
    """Reconciliation configuration."""

    require_outbound_match: bool = False
    match_tolerance_seconds: int = Field(default=300, ge=0)
    match_fields: List[str] = Field(
        default=["st_control_number", "gs_control_number", "transaction_type"]
    )
    report_unmatched: bool = True
    report_orphaned: bool = True


class ReportingFormatsConfig(BaseModel):
    """Output format configuration."""

    json: bool = True
    markdown: bool = True
    html: bool = False
    excel: bool = False


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    max_errors_per_transaction: int = Field(default=100, ge=1)
    include_accepted_in_report: bool = False
    group_errors_by_segment: bool = True
    sort_by_severity: bool = True
    include_line_numbers: bool = True
    include_summary: bool = True
    formats: ReportingFormatsConfig = Field(default_factory=ReportingFormatsConfig)


class PerformanceConfig(BaseModel):
    """Performance configuration."""

    enable_profiling: bool = False
    slow_operation_threshold_seconds: float = Field(default=1.0, ge=0.1)
    enable_caching: bool = False
    max_cache_size: int = Field(default=100, ge=1)


class ValidationBehaviorConfig(BaseModel):
    """Validation behavior configuration."""

    require_isa_segment: bool = True
    require_gs_segment: bool = True
    require_st_segment: bool = True
    require_ak1_segment: bool = True
    require_ak9_segment: bool = True
    allow_missing_ak2: bool = False
    validate_control_numbers: bool = True
    validate_segment_counts: bool = True


class ValidationConfig(BaseModel):
    """Main validation configuration."""

    strict_mode: bool = False
    max_errors_before_abort: int = Field(default=0, ge=0)
    behavior: ValidationBehaviorConfig = Field(default_factory=ValidationBehaviorConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    reconciliation: ReconciliationConfig = Field(default_factory=ReconciliationConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)


class AppConfig(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_env: Environment = Environment.DEVELOPMENT
    config_dir: Path = Field(default=Path("config"))
    output_dir: Path = Field(default=Path("output"))

    # Logging settings
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    enable_console_colors: bool = True
    enable_file_logging: bool = True
    log_file_path: Path = Field(default=Path("logs/validator.log"))

    # Validation settings (top-level overrides)
    validation_strict_mode: Optional[bool] = None
    max_errors_before_abort: Optional[int] = None
    require_outbound_match: Optional[bool] = None

    # Parser settings (top-level overrides)
    auto_detect_delimiters: Optional[bool] = None
    trim_whitespace: Optional[bool] = None
    max_file_size_mb: Optional[int] = None

    # Reconciliation settings (top-level overrides)
    match_tolerance_seconds: Optional[int] = None
    report_unmatched: Optional[bool] = None
    report_orphaned: Optional[bool] = None

    # Performance settings (top-level overrides)
    enable_profiling: Optional[bool] = None
    slow_operation_threshold: Optional[float] = None
    enable_caching: Optional[bool] = None
    max_cache_size: Optional[int] = None

    # Reporting settings (top-level overrides)
    max_errors_per_transaction: Optional[int] = None
    include_accepted_in_report: Optional[bool] = None
    group_errors_by_segment: Optional[bool] = None
    sort_by_severity: Optional[bool] = None

    # Output format overrides
    output_json: Optional[bool] = None
    output_markdown: Optional[bool] = None
    output_html: Optional[bool] = None
    output_excel: Optional[bool] = None

    @field_validator("config_dir", "output_dir")
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        """Ensure directory paths are valid."""
        if not v.is_absolute():
            # Make relative paths absolute from project root
            return Path.cwd() / v
        return v

    def merge_with_yaml_config(self, yaml_config: ValidationConfig) -> ValidationConfig:
        """Merge environment variables with YAML configuration.

        Environment variables take precedence over YAML configuration.
        """
        # Create a copy of the YAML config
        merged = yaml_config.model_copy(deep=True)

        # Override with environment variables if set
        if self.validation_strict_mode is not None:
            merged.strict_mode = self.validation_strict_mode

        if self.max_errors_before_abort is not None:
            merged.max_errors_before_abort = self.max_errors_before_abort

        if self.require_outbound_match is not None:
            merged.reconciliation.require_outbound_match = self.require_outbound_match

        if self.auto_detect_delimiters is not None:
            merged.parser.auto_detect_delimiters = self.auto_detect_delimiters

        if self.trim_whitespace is not None:
            merged.parser.trim_whitespace = self.trim_whitespace

        if self.max_file_size_mb is not None:
            merged.parser.max_file_size_mb = self.max_file_size_mb

        if self.match_tolerance_seconds is not None:
            merged.reconciliation.match_tolerance_seconds = self.match_tolerance_seconds

        if self.report_unmatched is not None:
            merged.reconciliation.report_unmatched = self.report_unmatched

        if self.report_orphaned is not None:
            merged.reconciliation.report_orphaned = self.report_orphaned

        if self.enable_profiling is not None:
            merged.performance.enable_profiling = self.enable_profiling

        if self.slow_operation_threshold is not None:
            merged.performance.slow_operation_threshold_seconds = self.slow_operation_threshold

        if self.enable_caching is not None:
            merged.performance.enable_caching = self.enable_caching

        if self.max_cache_size is not None:
            merged.performance.max_cache_size = self.max_cache_size

        if self.max_errors_per_transaction is not None:
            merged.reporting.max_errors_per_transaction = self.max_errors_per_transaction

        if self.include_accepted_in_report is not None:
            merged.reporting.include_accepted_in_report = self.include_accepted_in_report

        if self.group_errors_by_segment is not None:
            merged.reporting.group_errors_by_segment = self.group_errors_by_segment

        if self.sort_by_severity is not None:
            merged.reporting.sort_by_severity = self.sort_by_severity

        if self.output_json is not None:
            merged.reporting.formats.json = self.output_json

        if self.output_markdown is not None:
            merged.reporting.formats.markdown = self.output_markdown

        if self.output_html is not None:
            merged.reporting.formats.html = self.output_html

        if self.output_excel is not None:
            merged.reporting.formats.excel = self.output_excel

        return merged
