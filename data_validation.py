"""
LeadForge AI - Data Validation Module
Validates and sanitizes lead data to prevent corruption and ensure quality
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass


def validate_phone(phone: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate and normalize phone number

    Args:
        phone: Phone number string

    Returns:
        (is_valid, normalized_phone, error_message)
    """
    if not phone:
        return False, "", "Phone number is required"

    # Remove all non-numeric characters
    cleaned = re.sub(r'[^\d]', '', str(phone))

    # Check length (should be 10 or 11 digits)
    if len(cleaned) < 10 or len(cleaned) > 11:
        return False, phone, f"Invalid phone length: {len(cleaned)} digits"

    # Check if all zeros
    if cleaned == '0' * len(cleaned):
        return False, phone, "Phone number cannot be all zeros"

    # Format as (XXX) XXX-XXXX
    if len(cleaned) == 10:
        normalized = f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
    else:  # 11 digits (assume country code)
        normalized = f"+{cleaned[0]} ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"

    return True, normalized, ""


def validate_email(email: str) -> Tuple[bool, str, str]:
    """
    Validate email address

    Args:
        email: Email address string

    Returns:
        (is_valid, normalized_email, error_message)
    """
    if not email:
        return True, "", ""  # Email is optional

    email = str(email).strip().lower()

    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, email, f"Invalid email format: {email}"

    # Check for common typos
    common_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    domain = email.split('@')[-1]
    if domain not in common_domains:
        logger.warning(f"Unusual email domain: {domain}")

    return True, email, ""


def validate_url(url: str) -> Tuple[bool, str, str]:
    """
    Validate and normalize URL

    Args:
        url: URL string

    Returns:
        (is_valid, normalized_url, error_message)
    """
    if not url:
        return True, "", ""  # URL is optional

    url = str(url).strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Basic URL validation
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    if not re.match(pattern, url):
        return False, url, f"Invalid URL format: {url}"

    return True, url, ""


def validate_business_name(name: str) -> Tuple[bool, str, str]:
    """
    Validate business name

    Args:
        name: Business name string

    Returns:
        (is_valid, normalized_name, error_message)
    """
    if not name:
        return False, "", "Business name is required"

    name = str(name).strip()

    # Check minimum length
    if len(name) < 2:
        return False, name, "Business name too short (min 2 characters)"

    # Check maximum length
    if len(name) > 200:
        return False, name, "Business name too long (max 200 characters)"

    # Remove excessive whitespace
    name = ' '.join(name.split())

    # Check for placeholder text
    placeholders = ['unknown', 'n/a', 'tbd', 'to be determined', 'null']
    if name.lower() in placeholders:
        return False, name, f"Business name cannot be '{name}'"

    return True, name, ""


def validate_location(location: str) -> Tuple[bool, str, str]:
    """
    Validate location

    Args:
        location: Location string

    Returns:
        (is_valid, normalized_location, error_message)
    """
    if not location:
        return True, "", ""  # Location is optional

    location = str(location).strip()

    # Check minimum length
    if len(location) < 2:
        return False, location, "Location too short"

    # Check for state pattern (City, ST)
    if ',' in location:
        parts = [p.strip() for p in location.split(',')]
        if len(parts) >= 2:
            # Validate state code
            state = parts[-1].upper()
            if len(state) == 2 and not state.isalpha():
                return False, location, "Invalid state code"

    return True, location, ""


def validate_lead(lead: Dict[str, Any]) -> Tuple[bool, Dict[str, str], List[str]]:
    """
    Validate a complete lead record

    Args:
        lead: Lead dictionary

    Returns:
        (is_valid, normalized_lead, error_messages)
    """
    errors = []
    normalized = lead.copy()

    # Validate business name
    is_valid, name, error = validate_business_name(lead.get('business_name', ''))
    if not is_valid:
        errors.append(error)
    else:
        normalized['business_name'] = name

    # Validate phone
    is_valid, phone, error = validate_phone(lead.get('phone', ''))
    if not is_valid:
        errors.append(error)
    else:
        normalized['phone'] = phone

    # Validate email (optional)
    is_valid, email, error = validate_email(lead.get('email', ''))
    if not is_valid:
        errors.append(error)
    else:
        normalized['email'] = email

    # Validate website (optional)
    is_valid, website, error = validate_url(lead.get('website', ''))
    if not is_valid:
        errors.append(error)
    else:
        normalized['website'] = website

    # Validate location
    is_valid, location, error = validate_location(lead.get('location', ''))
    if not is_valid:
        errors.append(error)
    else:
        normalized['location'] = location

    # Validate score
    score = lead.get('score', 0)
    try:
        score = int(score)
        if score < 0 or score > 100:
            errors.append(f"Score must be 0-100, got {score}")
        else:
            normalized['score'] = score
    except (ValueError, TypeError):
        errors.append(f"Invalid score: {score}")

    # Add validation timestamp
    normalized['validated_at'] = datetime.now().isoformat()

    is_valid = len(errors) == 0
    return is_valid, normalized, errors


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    text = str(text)

    # Truncate to max length
    if len(text) > max_length:
        logger.warning(f"Input truncated from {len(text)} to {max_length} characters")
        text = text[:max_length]

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove excessive whitespace
    text = ' '.join(text.split())

    return text.strip()


def validate_leads_batch(leads: List[Dict]) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Validate a batch of leads

    Args:
        leads: List of lead dictionaries

    Returns:
        (valid_leads, invalid_leads, summary_errors)
    """
    valid_leads = []
    invalid_leads = []
    all_errors = []

    for i, lead in enumerate(leads):
        is_valid, normalized, errors = validate_lead(lead)

        if is_valid:
            valid_leads.append(normalized)
        else:
            invalid_leads.append(normalized)
            all_errors.append(f"Lead {i + 1}: {', '.join(errors)}")

    logger.info(f"Validated {len(leads)} leads: {len(valid_leads)} valid, {len(invalid_leads)} invalid")

    return valid_leads, invalid_leads, all_errors
