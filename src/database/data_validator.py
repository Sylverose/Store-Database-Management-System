"""
Compact data validation pipeline using utility-driven approach.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Import our utilities
from ..utils.common_utils import DataUtils

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

class DataType(Enum):
    """Supported data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    EMAIL = "email"
    CATEGORICAL = "categorical"

@dataclass
class ValidationRule:
    """Validation rule definition."""
    field_name: str
    data_type: DataType
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List] = None

@dataclass
class ValidationResult:
    """Validation result with issues."""
    is_valid: bool
    issues: List[Dict] = None
    summary: Dict = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class DataValidator:
    """Compact data validator using utility functions."""
    
    def __init__(self):
        self.rules = {}
        self.stats = DataUtils.create_stats_tracker()
    
    def add_rule(self, rule: ValidationRule):
        """Add validation rule."""
        self.rules[rule.field_name] = rule
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Validate entire DataFrame."""
        issues = []
        
        # Schema validation
        missing_columns = set(self.rules.keys()) - set(df.columns)
        for col in missing_columns:
            if self.rules[col].required:
                issues.append({
                    'type': 'missing_column',
                    'column': col,
                    'severity': ValidationSeverity.ERROR.value,
                    'message': f"Required column '{col}' is missing"
                })
        
        # Validate each column
        for col_name, rule in self.rules.items():
            if col_name in df.columns:
                col_issues = self._validate_column(df[col_name], rule)
                issues.extend(col_issues)
        
        # Create summary
        summary = self._create_summary(issues, len(df))
        
        return ValidationResult(
            is_valid=not any(issue['severity'] in ['error', 'critical'] for issue in issues),
            issues=issues,
            summary=summary
        )
    
    def _validate_column(self, series: pd.Series, rule: ValidationRule) -> List[Dict]:
        """Validate a column against its rule."""
        issues = []
        col_name = rule.field_name
        
        # Check for nulls
        null_count = series.isnull().sum()
        if null_count > 0 and rule.required:
            issues.append({
                'type': 'null_values',
                'column': col_name,
                'count': int(null_count),
                'severity': ValidationSeverity.ERROR.value,
                'message': f"Column '{col_name}' has {null_count} null values"
            })
        
        # Type validation
        valid_series = series.dropna()
        if not valid_series.empty:
            type_issues = self._validate_data_type(valid_series, rule)
            issues.extend(type_issues)
        
        return issues
    
    def _validate_data_type(self, series: pd.Series, rule: ValidationRule) -> List[Dict]:
        """Validate data type constraints."""
        issues = []
        col_name = rule.field_name
        
        if rule.data_type == DataType.INTEGER:
            non_int = ~series.apply(lambda x: str(x).isdigit() if pd.notna(x) else True)
            if non_int.any():
                issues.append({
                    'type': 'invalid_integer',
                    'column': col_name,
                    'count': int(non_int.sum()),
                    'severity': ValidationSeverity.ERROR.value,
                    'message': f"Column '{col_name}' has non-integer values"
                })
        
        elif rule.data_type == DataType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = ~series.astype(str).str.match(email_pattern, na=False)
            if invalid_emails.any():
                issues.append({
                    'type': 'invalid_email',
                    'column': col_name,
                    'count': int(invalid_emails.sum()),
                    'severity': ValidationSeverity.ERROR.value,
                    'message': f"Column '{col_name}' has invalid email formats"
                })
        
        # Length validation for strings
        if rule.data_type == DataType.STRING:
            if rule.min_length is not None:
                too_short = series.astype(str).str.len() < rule.min_length
                if too_short.any():
                    issues.append({
                        'type': 'string_too_short',
                        'column': col_name,
                        'count': int(too_short.sum()),
                        'severity': ValidationSeverity.WARNING.value,
                        'message': f"Column '{col_name}' has values shorter than {rule.min_length}"
                    })
            
            if rule.max_length is not None:
                too_long = series.astype(str).str.len() > rule.max_length
                if too_long.any():
                    issues.append({
                        'type': 'string_too_long',
                        'column': col_name,
                        'count': int(too_long.sum()),
                        'severity': ValidationSeverity.ERROR.value,
                        'message': f"Column '{col_name}' has values longer than {rule.max_length}"
                    })
        
        # Value range validation
        if rule.min_value is not None or rule.max_value is not None:
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            if rule.min_value is not None:
                too_small = numeric_series < rule.min_value
                if too_small.any():
                    issues.append({
                        'type': 'value_too_small',
                        'column': col_name,
                        'count': int(too_small.sum()),
                        'severity': ValidationSeverity.WARNING.value,
                        'message': f"Column '{col_name}' has values below {rule.min_value}"
                    })
            
            if rule.max_value is not None:
                too_large = numeric_series > rule.max_value
                if too_large.any():
                    issues.append({
                        'type': 'value_too_large',
                        'column': col_name,
                        'count': int(too_large.sum()),
                        'severity': ValidationSeverity.WARNING.value,
                        'message': f"Column '{col_name}' has values above {rule.max_value}"
                    })
        
        # Allowed values validation
        if rule.allowed_values is not None:
            invalid_values = ~series.isin(rule.allowed_values)
            if invalid_values.any():
                issues.append({
                    'type': 'invalid_categorical_value',
                    'column': col_name,
                    'count': int(invalid_values.sum()),
                    'severity': ValidationSeverity.ERROR.value,
                    'message': f"Column '{col_name}' has values not in allowed set"
                })
        
        return issues
    
    def _create_summary(self, issues: List[Dict], total_rows: int) -> Dict:
        """Create validation summary."""
        severity_counts = {}
        for issue in issues:
            severity = issue['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_issues': len(issues),
            'total_rows': total_rows,
            'severity_counts': severity_counts,
            'has_errors': any(issue['severity'] in ['error', 'critical'] for issue in issues),
            'validation_passed': not any(issue['severity'] in ['error', 'critical'] for issue in issues)
        }
    
    def clean_dataframe(self, df: pd.DataFrame, fix_issues=True) -> pd.DataFrame:
        """Clean DataFrame based on validation rules."""
        cleaned_df = df.copy()
        
        if fix_issues:
            for col_name, rule in self.rules.items():
                if col_name in cleaned_df.columns:
                    cleaned_df[col_name] = self._clean_column(cleaned_df[col_name], rule)
        
        return cleaned_df
    
    def _clean_column(self, series: pd.Series, rule: ValidationRule):
        """Clean column based on its validation rule."""
        cleaned = series.copy()
        
        # Handle string length issues
        if rule.data_type == DataType.STRING and rule.max_length:
            mask = cleaned.astype(str).str.len() > rule.max_length
            cleaned.loc[mask] = cleaned.loc[mask].astype(str).str[:rule.max_length]
        
        # Handle categorical values
        if rule.allowed_values is not None:
            invalid_mask = ~cleaned.isin(rule.allowed_values)
            cleaned.loc[invalid_mask] = None  # Set invalid values to null
        
        return cleaned
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics."""
        return self.stats.copy()


# Convenience functions
def create_common_rules() -> Dict[str, ValidationRule]:
    """Create common validation rules for ETL tables."""
    return {
        'customer_id': ValidationRule('customer_id', DataType.INTEGER, required=True, min_value=1),
        'order_id': ValidationRule('order_id', DataType.INTEGER, required=True, min_value=1),
        'product_id': ValidationRule('product_id', DataType.INTEGER, required=True, min_value=1),
        'email': ValidationRule('email', DataType.EMAIL, required=False, max_length=255),
        'phone': ValidationRule('phone', DataType.STRING, required=False, min_length=10, max_length=20),
        'first_name': ValidationRule('first_name', DataType.STRING, required=True, min_length=1, max_length=100),
        'last_name': ValidationRule('last_name', DataType.STRING, required=True, min_length=1, max_length=100)
    }

def validate_csv_file(file_path: str, rules: Dict[str, ValidationRule]) -> ValidationResult:
    """Validate a CSV file with given rules."""
    try:
        df = pd.read_csv(file_path)
        validator = DataValidator()
        
        for rule in rules.values():
            validator.add_rule(rule)
        
        return validator.validate_dataframe(df)
        
    except Exception as e:
        logger.error(f"CSV validation failed: {e}")
        return ValidationResult(
            is_valid=False,
            issues=[{
                'type': 'file_error',
                'severity': ValidationSeverity.CRITICAL.value,
                'message': f"Failed to read/validate file: {str(e)}"
            }]
        )

# Factory function for backward compatibility
def create_data_validator():
    """Create a DataValidator instance."""
    return DataValidator()