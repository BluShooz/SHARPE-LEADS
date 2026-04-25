"""
LeadForge AI - Email Enrichment Module
Integrates Hunter.io and Abstract API for email discovery and validation
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Email discovery result"""
    email: str
    confidence_score: int  # 0-100
    source: str  # 'hunter_io', 'abstract_api', 'manual'
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    twitter: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone_number: Optional[str] = None
    verification_status: Optional[str] = None  # 'valid', 'invalid', 'accept_all', 'unknown'


class HunterEmailFinder:
    """
    Hunter.io API Integration for Email Discovery

    Free Tier: 25 searches/month + 50 verifications
    Docs: https://hunter.io/api/docs
    """

    def __init__(self, api_key: str):
        """
        Initialize Hunter.io client

        Args:
            api_key: Hunter.io API key
        """
        self.api_key = api_key
        self.base_url = "https://api.hunter.io/v2"
        self.requests_count = 0

    def find_emails(
        self,
        domain: str,
        company: Optional[str] = None,
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[bool, List[EmailResult], Optional[str]]:
        """
        Find email addresses for a company/domain

        Args:
            domain: Company domain (e.g., "example.com")
            company: Company name (optional)
            full_name: Full name for specific person search
            first_name: First name for specific person search
            last_name: Last name for specific person search

        Returns:
            (success, email_results, error_message)
        """
        try:
            # Domain search (find all emails at company)
            if not full_name and not first_name:
                return self._domain_search(domain, company)

            # Email finder (specific person)
            else:
                return self._email_finder(domain, first_name, last_name, full_name)

        except Exception as e:
            error_msg = f"Hunter.io search failed: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def _domain_search(
        self,
        domain: str,
        company: Optional[str] = None
    ) -> Tuple[bool, List[EmailResult], Optional[str]]:
        """Search all emails at a domain"""
        try:
            url = f"{self.base_url}/domain-search"
            params = {
                'domain': domain,
                'api_key': self.api_key
            }

            if company:
                params['company'] = company

            logger.info(f"Hunter.io domain search: {domain}")
            response = requests.get(url, params=params, timeout=10)
            self.requests_count += 1

            if response.status_code == 402:
                return False, [], "Hunter.io API credit limit reached"

            response.raise_for_status()
            data = response.json()

            if data.get('data') and data['data'].get('emails'):
                emails_data = data['data']['emails']
                results = []

                for email_data in emails_data[:10]:  # Limit to top 10 emails
                    result = EmailResult(
                        email=email_data.get('value', ''),
                        confidence_score=email_data.get('confidence', 50),
                        source='hunter_io',
                        first_name=email_data.get('first_name'),
                        last_name=email_data.get('last_name'),
                        position=email_data.get('position'),
                        twitter=email_data.get('twitter'),
                        linkedin_url=email_data.get('linkedin_url'),
                        phone_number=email_data.get('phone_number')
                    )
                    results.append(result)

                logger.info(f"Found {len(results)} emails for {domain}")
                return True, results, None
            else:
                logger.warning(f"No emails found for domain: {domain}")
                return True, [], "No emails found"

        except requests.exceptions.RequestException as e:
            error_msg = f"Hunter.io domain search error: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def _email_finder(
        self,
        domain: str,
        first_name: Optional[str],
        last_name: Optional[str],
        full_name: Optional[str]
    ) -> Tuple[bool, List[EmailResult], Optional[str]]:
        """Find email for a specific person"""
        try:
            url = f"{self.base_url}/email-finder"
            params = {
                'domain': domain,
                'api_key': self.api_key
            }

            if full_name:
                params['full_name'] = full_name
            else:
                if first_name:
                    params['first_name'] = first_name
                if last_name:
                    params['last_name'] = last_name

            logger.info(f"Hunter.io person search: {params}")
            response = requests.get(url, params=params, timeout=10)
            self.requests_count += 1

            if response.status_code == 402:
                return False, [], "Hunter.io API credit limit reached"

            response.raise_for_status()
            data = response.json()

            if data.get('data') and data['data'].get('email'):
                email_data = data['data']
                result = EmailResult(
                    email=email_data['email'],
                    confidence_score=email_data.get('confidence', 50),
                    source='hunter_io',
                    first_name=email_data.get('first_name'),
                    last_name=email_data.get('last_name'),
                    position=email_data.get('position'),
                    twitter=email_data.get('twitter'),
                    linkedin_url=email_data.get('linkedin_url'),
                    phone_number=email_data.get('phone_number')
                )
                logger.info(f"Found email: {result.email} (confidence: {result.confidence_score})")
                return True, [result], None
            else:
                logger.warning("No email found for person")
                return True, [], "No email found"

        except requests.exceptions.RequestException as e:
            error_msg = f"Hunter.io person search error: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def verify_email(self, email: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Verify email deliverability (Hunter.io verifier)

        Args:
            email: Email address to verify

        Returns:
            (success, verification_data, error_message)
        """
        try:
            url = f"{self.base_url}/email-verifier"
            params = {
                'email': email,
                'api_key': self.api_key
            }

            logger.info(f"Hunter.io verify: {email}")
            response = requests.get(url, params=params, timeout=10)
            self.requests_count += 1

            if response.status_code == 402:
                return False, {}, "Hunter.io API credit limit reached"

            response.raise_for_status()
            data = response.json()

            if data.get('data'):
                result = {
                    'email': email,
                    'status': data['data'].get('status'),  # 'valid', 'invalid', 'accept_all', 'unknown'
                    'score': data['data'].get('score', 0),
                    'domain': data['data'].get('domain'),
                    'accept_mail': data['data'].get('accept_mail', False),
                    'sources': data['data'].get('sources', []),
                    'mx_records': data['data'].get('mx_records', []),
                    'smtp_provider': data['data'].get('smtp_provider')
                }
                logger.info(f"Email verified: {email} - {result['status']}")
                return True, result, None
            else:
                return False, {}, "Verification failed"

        except requests.exceptions.RequestException as e:
            error_msg = f"Hunter.io verification error: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg

    def get_account_info(self) -> Tuple[bool, Dict, Optional[str]]:
        """Get Hunter.io account info and remaining credits"""
        try:
            url = f"{self.base_url}/account"
            params = {'api_key': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('data'):
                account_info = {
                    'plan_name': data['data'].get('plan', {}).get('name'),
                    'credits': {
                        'search': data['data'].get('plan', {}).get('credits', {}).get('search', {}).get('remaining', 0),
                        'verifier': data['data'].get('plan', {}).get('credits', {}).get('verifier', {}).get('remaining', 0)
                    }
                }
                return True, account_info, None

            return False, {}, "Failed to get account info"

        except Exception as e:
            return False, {}, str(e)


class AbstractEmailValidator:
    """
    Abstract API Email Validation

    Free Tier: 100 requests/month
    Paid Tier: $6.49/month for 1,000 requests

    Docs: https://app.abstractapi.com/api/email-validation/docs
    """

    def __init__(self, api_key: str):
        """
        Initialize Abstract API client

        Args:
            api_key: Abstract API key
        """
        self.api_key = api_key
        self.base_url = "https://emailvalidation.abstractapi.com/v1/validate"
        self.requests_count = 0

    def validate_email(self, email: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate email deliverability

        Args:
            email: Email address to validate

        Returns:
            (success, validation_data, error_message)
        """
        try:
            url = f"{self.base_url}/validate"
            params = {
                'api_key': self.api_key,
                'email': email
            }

            logger.info(f"Abstract API validate: {email}")
            response = requests.get(url, params=params, timeout=10)
            self.requests_count += 1

            response.raise_for_status()
            data = response.json()

            # Extract relevant validation data
            result = {
                'email': email,
                'is_valid_format': data.get('is_valid_format', {}).get('value', False),
                'is_deliverable': data.get('is_deliverable', {}).get('value', False),
                'is_mx_found': data.get('is_mx_found', {}).get('value', False),
                'is_smtp_valid': data.get('is_smtp_valid', {}).get('value', False),
                'quality_score': data.get('quality_score', 0),
                'domain': data.get('domain', {}).get('name', ''),
                'smtp_provider': data.get('smtp_provider', {}).get('value', ''),
                'is_catchall': data.get('is_catchall', {}).get('value', False),
                'is_disposable': data.get('is_disposable', {}).get('value', False),
                'is_free_email': data.get('is_free_email', {}).get('value', False),
            }

            # Determine overall status
            if result['is_deliverable']:
                result['status'] = 'valid'
            elif result['is_catchall']:
                result['status'] = 'accept_all'
            elif result['is_disposable']:
                result['status'] = 'disposable'
            else:
                result['status'] = 'invalid'

            logger.info(f"Email validated: {email} - {result['status']} (quality: {result['quality_score']})")
            return True, result, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Abstract API validation error: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg


class EmailEnrichmentService:
    """
    Combined email enrichment service using both Hunter.io and Abstract API
    """

    def __init__(
        self,
        hunter_api_key: Optional[str] = None,
        abstract_api_key: Optional[str] = None
    ):
        """
        Initialize email enrichment service

        Args:
            hunter_api_key: Hunter.io API key (optional)
            abstract_api_key: Abstract API key (optional)
        """
        self.hunter = HunterEmailFinder(hunter_api_key) if hunter_api_key else None

        # Abstract API validation is optional - don't fail if key is invalid
        self.validator = None
        if abstract_api_key:
            try:
                self.validator = AbstractEmailValidator(abstract_api_key)
                # Test the API to make sure it works
                import requests
                test_url = f"{self.validator.base_url}?api_key={abstract_api_key}&email=test@example.com"
                response = requests.get(test_url, timeout=5)
                if response.status_code != 200:
                    logger.warning("Abstract API key is invalid or not activated - using Hunter.io for validation only")
                    self.validator = None
            except Exception as e:
                logger.warning(f"Abstract API initialization failed: {e} - using Hunter.io for validation only")
                self.validator = None

        logger.info(f"EmailEnrichmentService initialized (Hunter: {bool(self.hunter)}, Abstract: {bool(self.validator)})")

    def discover_and_validate(
        self,
        domain: str,
        company: Optional[str] = None
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Discover emails for a company and validate them

        Args:
            domain: Company domain
            company: Company name (optional)

        Returns:
            (success, enriched_emails, error_message)
        """
        try:
            if not self.hunter:
                return False, [], "Hunter.io not configured"

            # Step 1: Discover emails
            success, emails, error = self.hunter.find_emails(domain, company)
            if not success:
                return False, [], error

            if not emails:
                return True, [], "No emails found"

            # Step 2: Validate discovered emails
            enriched_results = []
            for email_result in emails:
                enriched = {
                    'email': email_result.email,
                    'confidence_score': email_result.confidence_score,
                    'source': email_result.source,
                    'first_name': email_result.first_name,
                    'last_name': email_result.last_name,
                    'position': email_result.position,
                    'twitter': email_result.twitter,
                    'linkedin_url': email_result.linkedin_url,
                    'phone_number': email_result.phone_number,
                    'discovered_at': datetime.now().isoformat()
                }

                # Validate with Abstract API if available, otherwise use Hunter.io
                if self.validator:
                    _, validation_data, _ = self.validator.validate_email(email_result.email)
                    enriched.update({
                        'is_valid_format': validation_data.get('is_valid_format', False),
                        'is_deliverable': validation_data.get('is_deliverable', False),
                        'quality_score': validation_data.get('quality_score', 0),
                        'verification_status': validation_data.get('status', 'unknown'),
                        'validated_at': datetime.now().isoformat()
                    })
                else:
                    # Use Hunter.io verification
                    _, hunter_validation, _ = self.hunter.verify_email(email_result.email)
                    enriched['verification_status'] = hunter_validation.get('status', 'unknown')
                    enriched['verification_score'] = hunter_validation.get('score', 0)
                    enriched['validated_at'] = datetime.now().isoformat()

                enriched_results.append(enriched)

            logger.info(f"Enriched {len(enriched_results)} emails for {domain}")
            return True, enriched_results, None

        except Exception as e:
            error_msg = f"Email enrichment failed: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def bulk_discover(
        self,
        domains: List[str],
        companies: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Bulk email discovery for multiple domains

        Args:
            domains: List of domains to search
            companies: Optional list of company names (must match domains length)

        Returns:
            Dictionary mapping domain to discovered emails
        """
        results = {}

        for i, domain in enumerate(domains):
            company = companies[i] if companies and i < len(companies) else None
            success, emails, error = self.discover_and_validate(domain, company)

            results[domain] = emails if success else []

            if error:
                logger.error(f"Failed to discover emails for {domain}: {error}")

        return results

    def get_api_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        stats = {
            'hunter_io': {
                'configured': bool(self.hunter),
                'requests_count': self.hunter.requests_count if self.hunter else 0,
                'credits_remaining': {}
            },
            'abstract_api': {
                'configured': bool(self.validator),
                'requests_count': self.validator.requests_count if self.validator else 0
            }
        }

        # Get Hunter.io account info
        if self.hunter:
            success, account_info, _ = self.hunter.get_account_info()
            if success:
                stats['hunter_io']['credits_remaining'] = account_info.get('credits', {})

        return stats


# Singleton instance
email_enrichment_service = None


def get_email_service() -> EmailEnrichmentService:
    """Get or create email enrichment service singleton"""
    global email_enrichment_service

    if email_enrichment_service is None:
        hunter_key = os.getenv('HUNTER_IO_API_KEY')
        abstract_key = os.getenv('ABSTRACT_API_KEY')

        if not hunter_key and not abstract_key:
            logger.warning("No email API keys configured")

        email_enrichment_service = EmailEnrichmentService(
            hunter_api_key=hunter_key,
            abstract_api_key=abstract_key
        )

    return email_enrichment_service
