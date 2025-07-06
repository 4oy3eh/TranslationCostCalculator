"""
Translation Cost Calculator - Translator Repository

Data access layer for Translator and Client entities with specialized queries
for translator management and client relationships.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.repositories.base_repository import BaseRepository, RepositoryError
from core.models.translator import Translator, Client
from config.database import DatabaseManager


class TranslatorRepository(BaseRepository[Translator]):
    """Repository for Translator entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "translators"
    
    def _row_to_model(self, row: sqlite3.Row) -> Translator:
        """Convert database row to Translator model.
        
        Args:
            row: Database row
            
        Returns:
            Translator: Translator domain model
        """
        translator = Translator()
        translator.id = row['id']
        translator.name = row['name']
        translator.email = row['email']
        translator.phone = row['phone']
        translator.address = row['address']
        translator.company = row['company']
        translator.tax_id = row['tax_id']
        translator.payment_terms = row['payment_terms']
        translator.is_active = bool(row['is_active'])
        
        # Parse datetime fields
        if row['created_at']:
            translator.created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            translator.updated_at = datetime.fromisoformat(row['updated_at'])
        
        return translator
    
    def _model_to_dict(self, model: Translator) -> Dict[str, Any]:
        """Convert Translator model to dictionary for database operations.
        
        Args:
            model: Translator model
            
        Returns:
            Dict[str, Any]: Translator data dictionary
        """
        data = {
            'id': model.id,
            'name': model.name,
            'email': model.email,
            'phone': model.phone,
            'address': model.address,
            'company': model.company,
            'tax_id': model.tax_id,
            'payment_terms': model.payment_terms,
            'is_active': model.is_active
        }
        
        # Add timestamps if present
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
        
        return data
    
    def find_by_name(self, name: str) -> Optional[Translator]:
        """Find translator by exact name.
        
        Args:
            name: Translator name
            
        Returns:
            Optional[Translator]: Translator or None if not found
        """
        return self.find_one_by_field('name', name)
    
    def find_by_email(self, email: str) -> Optional[Translator]:
        """Find translator by email address.
        
        Args:
            email: Email address
            
        Returns:
            Optional[Translator]: Translator or None if not found
        """
        return self.find_one_by_field('email', email)
    
    def find_active_translators(self) -> List[Translator]:
        """Find all active translators.
        
        Returns:
            List[Translator]: List of active translators
        """
        return self.find_by_field('is_active', True)
    
    def search_translators(self, search_term: str) -> List[Translator]:
        """Search translators by name, company, or email.
        
        Args:
            search_term: Search term
            
        Returns:
            List[Translator]: Matching translators
        """
        search_pattern = f"%{search_term}%"
        query = """
        SELECT * FROM translators 
        WHERE name LIKE ? OR company LIKE ? OR email LIKE ?
        ORDER BY name
        """
        
        cursor = self.execute_query(query, (search_pattern, search_pattern, search_pattern))
        translators = []
        
        if cursor:
            for row in cursor.fetchall():
                translator = self._row_to_model(row)
                translators.append(translator)
        
        return translators
    
    def get_translator_statistics(self, translator_id: int) -> Dict[str, Any]:
        """Get statistics for a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = {
            'project_count': 0,
            'rate_count': 0,
            'language_pairs': [],
            'clients': []
        }
        
        # Get project count
        query = "SELECT COUNT(*) as count FROM projects WHERE translator_id = ?"
        cursor = self.execute_query(query, (translator_id,))
        if cursor:
            result = cursor.fetchone()
            stats['project_count'] = result['count'] if result else 0
        
        # Get rate count
        query = "SELECT COUNT(*) as count FROM translator_rates WHERE translator_id = ?"
        cursor = self.execute_query(query, (translator_id,))
        if cursor:
            result = cursor.fetchone()
            stats['rate_count'] = result['count'] if result else 0
        
        # Get language pairs
        query = """
        SELECT DISTINCT lp.source_language, lp.target_language
        FROM translator_rates tr
        JOIN language_pairs lp ON tr.language_pair_id = lp.id
        WHERE tr.translator_id = ?
        """
        cursor = self.execute_query(query, (translator_id,))
        if cursor:
            for row in cursor.fetchall():
                pair = f"{row['source_language']}>{row['target_language']}"
                stats['language_pairs'].append(pair)
        
        # Get clients
        query = """
        SELECT DISTINCT c.name
        FROM translator_rates tr
        JOIN clients c ON tr.client_id = c.id
        WHERE tr.translator_id = ? AND tr.client_id IS NOT NULL
        """
        cursor = self.execute_query(query, (translator_id,))
        if cursor:
            for row in cursor.fetchall():
                stats['clients'].append(row['name'])
        
        return stats
    
    def deactivate_translator(self, translator_id: int) -> bool:
        """Deactivate a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            bool: True if successful
        """
        translator = self.find_by_id(translator_id)
        if not translator:
            return False
        
        translator.deactivate()
        updated = self.update(translator)
        return updated is not None
    
    def activate_translator(self, translator_id: int) -> bool:
        """Activate a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            bool: True if successful
        """
        translator = self.find_by_id(translator_id)
        if not translator:
            return False
        
        translator.activate()
        updated = self.update(translator)
        return updated is not None
    
    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if translator name already exists.
        
        Args:
            name: Translator name to check
            exclude_id: ID to exclude from check (for updates)
            
        Returns:
            bool: True if name exists
        """
        query = "SELECT 1 FROM translators WHERE name = ?"
        parameters = [name]
        
        if exclude_id:
            query += " AND id != ?"
            parameters.append(exclude_id)
        
        cursor = self.execute_query(query, tuple(parameters))
        return cursor is not None and cursor.fetchone() is not None
    
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            exclude_id: ID to exclude from check (for updates)
            
        Returns:
            bool: True if email exists
        """
        if not email:
            return False
        
        query = "SELECT 1 FROM translators WHERE email = ?"
        parameters = [email]
        
        if exclude_id:
            query += " AND id != ?"
            parameters.append(exclude_id)
        
        cursor = self.execute_query(query, tuple(parameters))
        return cursor is not None and cursor.fetchone() is not None


class ClientRepository(BaseRepository[Client]):
    """Repository for Client entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "clients"
    
    def _row_to_model(self, row: sqlite3.Row) -> Client:
        """Convert database row to Client model.
        
        Args:
            row: Database row
            
        Returns:
            Client: Client domain model
        """
        client = Client()
        client.id = row['id']
        client.name = row['name']
        client.contact_person = row['contact_person']
        client.email = row['email']
        client.phone = row['phone']
        client.address = row['address']
        client.company_registration = row['company_registration']
        client.tax_id = row['tax_id']
        client.payment_terms = row['payment_terms']
        client.is_active = bool(row['is_active'])
        
        # Parse datetime fields
        if row['created_at']:
            client.created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            client.updated_at = datetime.fromisoformat(row['updated_at'])
        
        return client
    
    def _model_to_dict(self, model: Client) -> Dict[str, Any]:
        """Convert Client model to dictionary for database operations.
        
        Args:
            model: Client model
            
        Returns:
            Dict[str, Any]: Client data dictionary
        """
        data = {
            'id': model.id,
            'name': model.name,
            'contact_person': model.contact_person,
            'email': model.email,
            'phone': model.phone,
            'address': model.address,
            'company_registration': model.company_registration,
            'tax_id': model.tax_id,
            'payment_terms': model.payment_terms,
            'is_active': model.is_active
        }
        
        # Add timestamps if present
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
        
        return data
    
    def find_by_name(self, name: str) -> Optional[Client]:
        """Find client by exact name.
        
        Args:
            name: Client name
            
        Returns:
            Optional[Client]: Client or None if not found
        """
        return self.find_one_by_field('name', name)
    
    def find_active_clients(self) -> List[Client]:
        """Find all active clients.
        
        Returns:
            List[Client]: List of active clients
        """
        return self.find_by_field('is_active', True)
    
    def search_clients(self, search_term: str) -> List[Client]:
        """Search clients by name, contact person, or email.
        
        Args:
            search_term: Search term
            
        Returns:
            List[Client]: Matching clients
        """
        search_pattern = f"%{search_term}%"
        query = """
        SELECT * FROM clients 
        WHERE name LIKE ? OR contact_person LIKE ? OR email LIKE ?
        ORDER BY name
        """
        
        cursor = self.execute_query(query, (search_pattern, search_pattern, search_pattern))
        clients = []
        
        if cursor:
            for row in cursor.fetchall():
                client = self._row_to_model(row)
                clients.append(client)
        
        return clients
    
    def get_client_statistics(self, client_id: int) -> Dict[str, Any]:
        """Get statistics for a client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = {
            'project_count': 0,
            'rate_count': 0,
            'translators': []
        }
        
        # Get project count
        query = "SELECT COUNT(*) as count FROM projects WHERE client_id = ?"
        cursor = self.execute_query(query, (client_id,))
        if cursor:
            result = cursor.fetchone()
            stats['project_count'] = result['count'] if result else 0
        
        # Get rate count (client-specific rates)
        query = "SELECT COUNT(*) as count FROM translator_rates WHERE client_id = ?"
        cursor = self.execute_query(query, (client_id,))
        if cursor:
            result = cursor.fetchone()
            stats['rate_count'] = result['count'] if result else 0
        
        # Get translators working with this client
        query = """
        SELECT DISTINCT t.name
        FROM translator_rates tr
        JOIN translators t ON tr.translator_id = t.id
        WHERE tr.client_id = ?
        """
        cursor = self.execute_query(query, (client_id,))
        if cursor:
            for row in cursor.fetchall():
                stats['translators'].append(row['name'])
        
        return stats
    
    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if client name already exists.
        
        Args:
            name: Client name to check
            exclude_id: ID to exclude from check (for updates)
            
        Returns:
            bool: True if name exists
        """
        query = "SELECT 1 FROM clients WHERE name = ?"
        parameters = [name]
        
        if exclude_id:
            query += " AND id != ?"
            parameters.append(exclude_id)
        
        cursor = self.execute_query(query, tuple(parameters))
        return cursor is not None and cursor.fetchone() is not None
    
    def get_clients_with_rates(self, translator_id: int) -> List[Client]:
        """Get clients that have specific rates with a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Client]: Clients with specific rates
        """
        query = """
        SELECT DISTINCT c.*
        FROM clients c
        JOIN translator_rates tr ON c.id = tr.client_id
        WHERE tr.translator_id = ? AND c.is_active = 1
        ORDER BY c.name
        """
        
        cursor = self.execute_query(query, (translator_id,))
        clients = []
        
        if cursor:
            for row in cursor.fetchall():
                client = self._row_to_model(row)
                clients.append(client)
        
        return clients
    
    def get_clients_by_translator(self, translator_id: int) -> List[Client]:
        """Get all clients that have worked with a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Client]: Clients associated with translator
        """
        query = """
        SELECT DISTINCT c.*
        FROM clients c
        JOIN projects p ON c.id = p.client_id
        WHERE p.translator_id = ? AND c.is_active = 1
        ORDER BY c.name
        """
        
        cursor = self.execute_query(query, (translator_id,))
        clients = []
        
        if cursor:
            for row in cursor.fetchall():
                client = self._row_to_model(row)
                clients.append(client)
        
        return clients