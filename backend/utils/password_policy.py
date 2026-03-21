"""
Password Policy Enforcement - TR-013

Enforces strong password requirements to prevent weak password attacks.

Requirements:
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Not commonly used passwords
- Not sequential characters (123, abc, etc.)

ALE Prevented: $3,000/year
"""

import re
from typing import Tuple, List
from backend.utils.logger import logger


# Common weak passwords (subset - full list would be 10k+)
COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456",
    "12345678",
    "qwerty",
    "abc123",
    "monkey",
    "1234567",
    "letmein",
    "trustno1",
    "dragon",
    "baseball",
    "iloveyou",
    "master",
    "sunshine",
    "ashley",
    "bailey",
    "passw0rd",
    "shadow",
    "123123",
    "654321",
    "superman",
    "qazwsx",
    "michael",
    "football",
    "welcome",
    "jesus",
    "ninja",
    "mustang",
    "admin",
    "password1",
    "changeme",
    "welcome123",
    "admin123",
}


class PasswordPolicy:
    """Enforce strong password policy"""

    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against policy.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check minimum length
        if len(password) < PasswordPolicy.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters long")

        # Check for uppercase letter
        if PasswordPolicy.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Check for lowercase letter
        if PasswordPolicy.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Check for digit
        if PasswordPolicy.REQUIRE_DIGIT and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        # Check for special character
        if PasswordPolicy.REQUIRE_SPECIAL and not re.search(
            r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/~`]', password
        ):
            errors.append("Password must contain at least one special character (!@#$%^&*, etc.)")

        # Check for common passwords (case-insensitive)
        if password.lower() in COMMON_PASSWORDS:
            errors.append("This password is too common. Please choose a more unique password")

        # Check for sequential characters
        if PasswordPolicy._has_sequential_chars(password):
            errors.append("Password cannot contain sequential characters (123, abc, etc.)")

        # Check for repeated characters (more than 3 in a row)
        if PasswordPolicy._has_repeated_chars(password, max_repeat=3):
            errors.append("Password cannot contain more than 3 repeated characters in a row")

        is_valid = len(errors) == 0

        if not is_valid:
            logger.info(f"Password validation failed: {len(errors)} policy violations")

        return is_valid, errors

    @staticmethod
    def _has_sequential_chars(password: str, min_length: int = 3) -> bool:
        """Check for sequential characters (123, abc, etc.)"""
        password_lower = password.lower()

        for i in range(len(password_lower) - min_length + 1):
            # Check for sequential numbers
            if password[i : i + min_length].isdigit():
                chars = [int(c) for c in password[i : i + min_length]]
                if all(chars[j] + 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True
                if all(chars[j] - 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True

            # Check for sequential letters
            if password_lower[i : i + min_length].isalpha():
                ords = [ord(c) for c in password_lower[i : i + min_length]]
                if all(ords[j] + 1 == ords[j + 1] for j in range(len(ords) - 1)):
                    return True
                if all(ords[j] - 1 == ords[j + 1] for j in range(len(ords) - 1)):
                    return True

        return False

    @staticmethod
    def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
        """Check for repeated characters"""
        count = 1
        prev_char = ""

        for char in password:
            if char == prev_char:
                count += 1
                if count > max_repeat:
                    return True
            else:
                count = 1
                prev_char = char

        return False

    @staticmethod
    def get_password_strength(password: str) -> dict:
        """
        Calculate password strength score.

        Returns:
            Dictionary with strength score (0-100) and feedback
        """
        score = 0
        feedback = []

        # Length score (up to 30 points)
        if len(password) >= 12:
            score += 15
        if len(password) >= 16:
            score += 10
        if len(password) >= 20:
            score += 5
        else:
            feedback.append("Consider using a longer password")

        # Character diversity (up to 40 points)
        if re.search(r"[A-Z]", password):
            score += 10
        else:
            feedback.append("Add uppercase letters")

        if re.search(r"[a-z]", password):
            score += 10
        else:
            feedback.append("Add lowercase letters")

        if re.search(r"\d", password):
            score += 10
        else:
            feedback.append("Add numbers")

        if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/~`]', password):
            score += 10
        else:
            feedback.append("Add special characters")

        # Uniqueness (up to 30 points)
        if password.lower() not in COMMON_PASSWORDS:
            score += 15
        else:
            feedback.append("This password is too common")

        if not PasswordPolicy._has_sequential_chars(password):
            score += 10
        else:
            feedback.append("Avoid sequential characters")

        if not PasswordPolicy._has_repeated_chars(password):
            score += 5
        else:
            feedback.append("Avoid repeated characters")

        # Determine strength level
        if score >= 80:
            strength = "strong"
        elif score >= 60:
            strength = "medium"
        else:
            strength = "weak"

        return {"score": score, "strength": strength, "feedback": feedback}


# Global instance
password_policy = PasswordPolicy()
