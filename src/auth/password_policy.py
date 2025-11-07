"""
Password Policy Validator
Enforces password strength requirements
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class PasswordRequirements:
    """Password policy requirements"""
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"


class PasswordPolicyValidator:
    """Validates passwords against security policy"""
    
    def __init__(self, requirements: PasswordRequirements = None):
        """
        Initialize password validator
        
        Args:
            requirements: Password requirements (uses defaults if None)
        """
        self.requirements = requirements or PasswordRequirements()
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against policy
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.requirements.min_length:
            errors.append(f"Password must be at least {self.requirements.min_length} characters long")
        
        # Check uppercase requirement
        if self.requirements.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase requirement
        if self.requirements.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check digit requirement
        if self.requirements.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check special character requirement
        if self.requirements.require_special:
            special_pattern = f"[{re.escape(self.requirements.special_chars)}]"
            if not re.search(special_pattern, password):
                errors.append(f"Password must contain at least one special character ({self.requirements.special_chars})")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', 'Password1', 'password123', 'admin', 'Admin123',
            '12345678', 'qwerty123', 'letmein', 'welcome', 'monkey123'
        ]
        if password.lower() in [wp.lower() for wp in weak_passwords]:
            errors.append("Password is too common and easily guessable")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_requirements_text(self) -> str:
        """Get human-readable password requirements"""
        requirements = []
        
        requirements.append(f"At least {self.requirements.min_length} characters long")
        
        if self.requirements.require_uppercase:
            requirements.append("At least one uppercase letter (A-Z)")
        
        if self.requirements.require_lowercase:
            requirements.append("At least one lowercase letter (a-z)")
        
        if self.requirements.require_digit:
            requirements.append("At least one number (0-9)")
        
        if self.requirements.require_special:
            requirements.append(f"At least one special character ({self.requirements.special_chars})")
        
        return "\n".join(f"• {req}" for req in requirements)
    
    def calculate_strength(self, password: str) -> Tuple[str, int]:
        """
        Calculate password strength
        
        Args:
            password: Password to evaluate
            
        Returns:
            Tuple of (strength_label, strength_percentage)
        """
        strength = 0
        
        # Length scoring (up to 30 points)
        if len(password) >= 12:
            strength += 30
        elif len(password) >= 10:
            strength += 20
        elif len(password) >= 8:
            strength += 10
        
        # Character variety (up to 40 points)
        if re.search(r'[a-z]', password):
            strength += 10
        if re.search(r'[A-Z]', password):
            strength += 10
        if re.search(r'\d', password):
            strength += 10
        if re.search(f"[{re.escape(self.requirements.special_chars)}]", password):
            strength += 10
        
        # Additional complexity (up to 30 points)
        if len(set(password)) > len(password) * 0.7:  # Character diversity
            strength += 10
        if not any(password.lower().count(c * 3) for c in set(password)):  # No repeated chars
            strength += 10
        if len(password) >= 16:  # Extra length bonus
            strength += 10
        
        # Determine label
        if strength >= 80:
            label = "Very Strong"
        elif strength >= 60:
            label = "Strong"
        elif strength >= 40:
            label = "Medium"
        elif strength >= 20:
            label = "Weak"
        else:
            label = "Very Weak"
        
        return label, strength


# Global instance with default requirements
default_validator = PasswordPolicyValidator()
