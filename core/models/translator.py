"""
Translation Cost Calculator - Translator Domain Model

Translator entity with contact information and associated rates.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class Translator:
    """Translator domain model."""
    
    # Core identification
    id: Optional[int] = None
    name: str = ""
    email: Optional[str] = None
    
    # Contact information
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # Business information
    company: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize default values and validate data."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Clean and validate name
        self.name = self.name.strip()
        
        # Validate and normalize email
        if self.email:
            self.email = self.email.strip().lower()
            if not self.is_valid_email(self.email):
                self.email = None
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        if not email:
            return False
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_valid(self) -> bool:
        """Check if translator has all required fields.
        
        Returns:
            bool: True if translator is valid
        """
        return (
            bool(self.name.strip()) and
            len(self.name.strip()) >= 2
        )
    
    def get_display_name(self) -> str:
        """Get translator display name with company if available.
        
        Returns:
            str: Display name including company if present
        """
        if self.company:
            return f"{self.name} ({self.company})"
        return self.name
    
    def get_contact_info(self) -> dict:
        """Get formatted contact information.
        
        Returns:
            dict: Contact information dictionary
        """
        contact = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company': self.company
        }
        
        # Remove None values
        return {k: v for k, v in contact.items() if v is not None}
    
    def update_contact_info(self, **kwargs) -> None:
        """Update contact information fields.
        
        Args:
            **kwargs: Fields to update (email, phone, address, company, etc.)
        """
        for field, value in kwargs.items():
            if hasattr(self, field):
                if field == 'email' and value:
                    # Validate email before setting
                    cleaned_email = value.strip().lower()
                    if self.is_valid_email(cleaned_email):
                        setattr(self, field, cleaned_email)
                else:
                    setattr(self, field, value)
        
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Deactivate the translator."""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Activate the translator."""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert translator to dictionary for serialization.
        
        Returns:
            dict: Translator data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company': self.company,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Translator':
        """Create translator from dictionary data.
        
        Args:
            data: Dictionary containing translator data
            
        Returns:
            Translator: New translator instance
        """
        translator = cls()
        translator.id = data.get('id')
        translator.name = data.get('name', '')
        translator.email = data.get('email')
        translator.phone = data.get('phone')
        translator.address = data.get('address')
        translator.company = data.get('company')
        translator.tax_id = data.get('tax_id')
        translator.payment_terms = data.get('payment_terms')
        translator.is_active = data.get('is_active', True)
        
        # Parse datetime fields
        if data.get('created_at'):
            translator.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            translator.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return translator
    
    def __str__(self) -> str:
        """String representation of the translator."""
        return self.get_display_name()
    
    def __repr__(self) -> str:
        """Developer representation of the translator."""
        return f"Translator(id={self.id}, name='{self.name}', active={self.is_active})"


@dataclass
class Client:
    """Client domain model for rate hierarchy."""
    
    # Core identification
    id: Optional[int] = None
    name: str = ""
    
    # Contact information
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # Business information
    company_registration: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize default values and validate data."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Clean name
        self.name = self.name.strip()
        
        # Validate email
        if self.email:
            self.email = self.email.strip().lower()
            if not Translator.is_valid_email(self.email):
                self.email = None
    
    def is_valid(self) -> bool:
        """Check if client has all required fields.
        
        Returns:
            bool: True if client is valid
        """
        return (
            bool(self.name.strip()) and
            len(self.name.strip()) >= 2
        )
    
    def get_display_name(self) -> str:
        """Get client display name with contact person if available.
        
        Returns:
            str: Display name including contact person if present
        """
        if self.contact_person:
            return f"{self.name} (Contact: {self.contact_person})"
        return self.name
    
    def to_dict(self) -> dict:
        """Convert client to dictionary for serialization.
        
        Returns:
            dict: Client data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company_registration': self.company_registration,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Client':
        """Create client from dictionary data.
        
        Args:
            data: Dictionary containing client data
            
        Returns:
            Client: New client instance
        """
        client = cls()
        client.id = data.get('id')
        client.name = data.get('name', '')
        client.contact_person = data.get('contact_person')
        client.email = data.get('email')
        client.phone = data.get('phone')
        client.address = data.get('address')
        client.company_registration = data.get('company_registration')
        client.tax_id = data.get('tax_id')
        client.payment_terms = data.get('payment_terms')
        client.is_active = data.get('is_active', True)
        
        # Parse datetime fields
        if data.get('created_at'):
            client.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            client.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return client
    
    def __str__(self) -> str:
        """String representation of the client."""
        return self.get_display_name()
    
    def __repr__(self) -> str:
        """Developer representation of the client."""
        return f"Client(id={self.id}, name='{self.name}', active={self.is_active})"