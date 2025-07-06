"""
Translation Cost Calculator - Rate Repository

Data access layer for Rate and LanguagePair entities with specialized queries
for hierarchical rate resolution and rate management.
"""

import sqlite3
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from core.repositories.base_repository import BaseRepository, RepositoryError
from core.models.rate import Rate, LanguagePair, RateCalculator
from core.models.match_category import MatchCategoryType
from config.database import DatabaseManager


class RateRepository(BaseRepository[Rate]):
    """Repository for Rate entity operations with hierarchical rate support."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "translator_rates"
    
    def _row_to_model(self, row: sqlite3.Row) -> Rate:
        """Convert database row to Rate model.
        
        Args:
            row: Database row
            
        Returns:
            Rate: Rate domain model
        """
        rate = Rate()
        rate.id = row['id']
        rate.translator_id = row['translator_id']
        rate.client_id = row['client_id']
        rate.language_pair_id = row['language_pair_id']
        rate.match_category_id = row['match_category_id']
        rate.rate_per_word = Decimal(str(row['rate_per_word']))
        rate.minimum_fee = Decimal(str(row['minimum_fee']))
        rate.is_minimum_fee_enabled = bool(row['is_minimum_fee_enabled'])
        rate.currency = row['currency']
        
        # Parse datetime fields
        if row['created_at']:
            rate.created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            rate.updated_at = datetime.fromisoformat(row['updated_at'])
        
        return rate
    
    def _model_to_dict(self, model: Rate) -> Dict[str, Any]:
        """Convert Rate model to dictionary for database operations.
        
        Args:
            model: Rate model
            
        Returns:
            Dict[str, Any]: Rate data dictionary
        """
        data = {
            'id': model.id,
            'translator_id': model.translator_id,
            'client_id': model.client_id,
            'language_pair_id': model.language_pair_id,
            'match_category_id': model.match_category_id,
            'rate_per_word': float(model.rate_per_word),
            'minimum_fee': float(model.minimum_fee),
            'is_minimum_fee_enabled': model.is_minimum_fee_enabled,
            'currency': model.currency
        }
        
        # Add timestamps if present
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
        
        return data
    
    def find_by_translator(self, translator_id: int) -> List[Rate]:
        """Find all rates for a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Rate]: List of rates
        """
        return self.find_by_field('translator_id', translator_id)
    
    def find_by_client(self, translator_id: int, client_id: int) -> List[Rate]:
        """Find client-specific rates for a translator.
        
        Args:
            translator_id: Translator ID
            client_id: Client ID
            
        Returns:
            List[Rate]: List of client-specific rates
        """
        query = "SELECT * FROM translator_rates WHERE translator_id = ? AND client_id = ?"
        cursor = self.execute_query(query, (translator_id, client_id))
        rates = []
        
        if cursor:
            for row in cursor.fetchall():
                rate = self._row_to_model(row)
                rates.append(rate)
        
        return rates
    
    def find_general_rates(self, translator_id: int) -> List[Rate]:
        """Find general (non-client-specific) rates for a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Rate]: List of general rates
        """
        query = "SELECT * FROM translator_rates WHERE translator_id = ? AND client_id IS NULL"
        cursor = self.execute_query(query, (translator_id,))
        rates = []
        
        if cursor:
            for row in cursor.fetchall():
                rate = self._row_to_model(row)
                rates.append(rate)
        
        return rates
    
    def find_rate_for_project(self, translator_id: int, language_pair_id: int, 
                             match_category_id: int, client_id: Optional[int] = None) -> Optional[Rate]:
        """Find the best applicable rate using hierarchy resolution.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            match_category_id: Match category ID
            client_id: Optional client ID for client-specific rates
            
        Returns:
            Optional[Rate]: Best applicable rate or None
        """
        # Get all applicable rates
        query = """
        SELECT * FROM translator_rates 
        WHERE translator_id = ? AND language_pair_id = ? AND match_category_id = ?
        ORDER BY 
            CASE WHEN client_id IS NOT NULL THEN 1 ELSE 2 END,
            created_at DESC
        """
        
        cursor = self.execute_query(query, (translator_id, language_pair_id, match_category_id))
        rates = []
        
        if cursor:
            for row in cursor.fetchall():
                rate = self._row_to_model(row)
                rates.append(rate)
        
        # Use rate calculator for hierarchy resolution
        return RateCalculator.resolve_rate_hierarchy(
            rates, translator_id, language_pair_id, match_category_id, client_id
        )
    
    def get_rate_matrix(self, translator_id: int, client_id: Optional[int] = None) -> Dict[str, Dict[str, Rate]]:
        """Get complete rate matrix for a translator.
        
        Args:
            translator_id: Translator ID
            client_id: Optional client ID for client-specific rates
            
        Returns:
            Dict[str, Dict[str, Rate]]: Rate matrix organized by language pair and category
        """
        # Build query based on whether client_id is specified
        if client_id:
            query = """
            SELECT r.*, lp.source_language, lp.target_language, mc.name as category_name
            FROM translator_rates r
            JOIN language_pairs lp ON r.language_pair_id = lp.id
            JOIN match_categories mc ON r.match_category_id = mc.id
            WHERE r.translator_id = ? AND (r.client_id = ? OR r.client_id IS NULL)
            ORDER BY lp.source_language, lp.target_language, mc.display_order,
                     CASE WHEN r.client_id IS NOT NULL THEN 1 ELSE 2 END
            """
            parameters = (translator_id, client_id)
        else:
            query = """
            SELECT r.*, lp.source_language, lp.target_language, mc.name as category_name
            FROM translator_rates r
            JOIN language_pairs lp ON r.language_pair_id = lp.id
            JOIN match_categories mc ON r.match_category_id = mc.id
            WHERE r.translator_id = ? AND r.client_id IS NULL
            ORDER BY lp.source_language, lp.target_language, mc.display_order
            """
            parameters = (translator_id,)
        
        cursor = self.execute_query(query, parameters)
        rate_matrix = {}
        
        if cursor:
            for row in cursor.fetchall():
                language_pair = f"{row['source_language']}>{row['target_language']}"
                category_name = row['category_name']
                
                if language_pair not in rate_matrix:
                    rate_matrix[language_pair] = {}
                
                # Use hierarchical resolution for client-specific queries
                if client_id and category_name not in rate_matrix[language_pair]:
                    rate = self._row_to_model(row)
                    rate_matrix[language_pair][category_name] = rate
                elif not client_id:
                    rate = self._row_to_model(row)
                    rate_matrix[language_pair][category_name] = rate
        
        return rate_matrix
    
    def create_rate_set(self, translator_id: int, language_pair_id: int, 
                       rates_data: Dict[int, Decimal], client_id: Optional[int] = None,
                       minimum_fee: Decimal = Decimal('0.00'), 
                       enable_minimum_fee: bool = False) -> List[Rate]:
        """Create a complete set of rates for all match categories.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            rates_data: Dictionary mapping match_category_id to rate_per_word
            client_id: Optional client ID for client-specific rates
            minimum_fee: Minimum fee for all rates
            enable_minimum_fee: Whether to enable minimum fee
            
        Returns:
            List[Rate]: Created rates
        """
        created_rates = []
        operations = []
        
        for match_category_id, rate_per_word in rates_data.items():
            # Check if rate already exists
            existing_rate = self._find_specific_rate(
                translator_id, language_pair_id, match_category_id, client_id
            )
            
            if existing_rate:
                self.logger.warning(
                    f"Rate already exists for translator {translator_id}, "
                    f"language_pair {language_pair_id}, category {match_category_id}, "
                    f"client {client_id}"
                )
                continue
            
            # Create new rate
            rate = Rate(
                translator_id=translator_id,
                client_id=client_id,
                language_pair_id=language_pair_id,
                match_category_id=match_category_id,
                rate_per_word=rate_per_word,
                minimum_fee=minimum_fee,
                is_minimum_fee_enabled=enable_minimum_fee
            )
            
            # Prepare insert operation
            data = self._model_to_dict(rate)
            del data['id']  # Remove ID for insert
            
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [data[col] for col in columns]
            
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            operations.append((query, tuple(values)))
        
        # Execute all inserts in a transaction
        if operations and self.execute_transaction(operations):
            # Fetch created rates
            created_rates = self.find_by_translator_and_language_pair(translator_id, language_pair_id)
            if client_id:
                created_rates = [r for r in created_rates if r.client_id == client_id]
            else:
                created_rates = [r for r in created_rates if r.client_id is None]
        
        return created_rates
    
    def update_rate_set(self, translator_id: int, language_pair_id: int,
                       rates_data: Dict[int, Decimal], client_id: Optional[int] = None) -> List[Rate]:
        """Update existing rates for a translator and language pair.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            rates_data: Dictionary mapping match_category_id to new rate_per_word
            client_id: Optional client ID for client-specific rates
            
        Returns:
            List[Rate]: Updated rates
        """
        updated_rates = []
        
        for match_category_id, new_rate in rates_data.items():
            rate = self._find_specific_rate(translator_id, language_pair_id, match_category_id, client_id)
            
            if rate:
                rate.update_rate(new_rate)
                updated_rate = self.update(rate)
                if updated_rate:
                    updated_rates.append(updated_rate)
        
        return updated_rates
    
    def delete_rate_set(self, translator_id: int, language_pair_id: int, 
                       client_id: Optional[int] = None) -> bool:
        """Delete all rates for a translator and language pair.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            client_id: Optional client ID for client-specific rates
            
        Returns:
            bool: True if deletion successful
        """
        if client_id:
            query = """
            DELETE FROM translator_rates 
            WHERE translator_id = ? AND language_pair_id = ? AND client_id = ?
            """
            parameters = (translator_id, language_pair_id, client_id)
        else:
            query = """
            DELETE FROM translator_rates 
            WHERE translator_id = ? AND language_pair_id = ? AND client_id IS NULL
            """
            parameters = (translator_id, language_pair_id)
        
        cursor = self.execute_query(query, parameters)
        
        if cursor and cursor.rowcount > 0:
            self.logger.info(f"Deleted {cursor.rowcount} rates for translator {translator_id}")
            return True
        
        return False
    
    def find_by_translator_and_language_pair(self, translator_id: int, language_pair_id: int) -> List[Rate]:
        """Find all rates for a translator and language pair.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            
        Returns:
            List[Rate]: List of rates
        """
        query = "SELECT * FROM translator_rates WHERE translator_id = ? AND language_pair_id = ?"
        cursor = self.execute_query(query, (translator_id, language_pair_id))
        rates = []
        
        if cursor:
            for row in cursor.fetchall():
                rate = self._row_to_model(row)
                rates.append(rate)
        
        return rates
    
    def get_rates_summary(self, translator_id: int) -> List[Dict[str, Any]]:
        """Get summary of all rates for a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Dict[str, Any]]: Rate summaries
        """
        query = """
        SELECT r.id, r.rate_per_word, r.minimum_fee, r.is_minimum_fee_enabled,
               lp.source_language, lp.target_language,
               mc.name as category_name, mc.display_order,
               c.name as client_name,
               CASE WHEN r.client_id IS NOT NULL THEN 1 ELSE 2 END as priority_level
        FROM translator_rates r
        JOIN language_pairs lp ON r.language_pair_id = lp.id
        JOIN match_categories mc ON r.match_category_id = mc.id
        LEFT JOIN clients c ON r.client_id = c.id
        WHERE r.translator_id = ?
        ORDER BY lp.source_language, lp.target_language, priority_level, mc.display_order
        """
        
        return self.execute_custom_query(query, (translator_id,))
    
    def _find_specific_rate(self, translator_id: int, language_pair_id: int, 
                           match_category_id: int, client_id: Optional[int] = None) -> Optional[Rate]:
        """Find specific rate by exact criteria.
        
        Args:
            translator_id: Translator ID
            language_pair_id: Language pair ID
            match_category_id: Match category ID
            client_id: Optional client ID
            
        Returns:
            Optional[Rate]: Specific rate or None
        """
        if client_id:
            query = """
            SELECT * FROM translator_rates 
            WHERE translator_id = ? AND language_pair_id = ? 
            AND match_category_id = ? AND client_id = ?
            """
            parameters = (translator_id, language_pair_id, match_category_id, client_id)
        else:
            query = """
            SELECT * FROM translator_rates 
            WHERE translator_id = ? AND language_pair_id = ? 
            AND match_category_id = ? AND client_id IS NULL
            """
            parameters = (translator_id, language_pair_id, match_category_id)
        
        cursor = self.execute_query(query, parameters)
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
        
        return None


class LanguagePairRepository(BaseRepository[LanguagePair]):
    """Repository for LanguagePair entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "language_pairs"
    
    def _row_to_model(self, row: sqlite3.Row) -> LanguagePair:
        """Convert database row to LanguagePair model.
        
        Args:
            row: Database row
            
        Returns:
            LanguagePair: LanguagePair domain model
        """
        pair = LanguagePair()
        pair.id = row['id']
        pair.source_language = row['source_language']
        pair.target_language = row['target_language']
        return pair
    
    def _model_to_dict(self, model: LanguagePair) -> Dict[str, Any]:
        """Convert LanguagePair model to dictionary for database operations.
        
        Args:
            model: LanguagePair model
            
        Returns:
            Dict[str, Any]: LanguagePair data dictionary
        """
        return {
            'id': model.id,
            'source_language': model.source_language,
            'target_language': model.target_language
        }
    
    def find_by_languages(self, source_lang: str, target_lang: str) -> Optional[LanguagePair]:
        """Find language pair by source and target languages.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Optional[LanguagePair]: Language pair or None
        """
        query = "SELECT * FROM language_pairs WHERE source_language = ? AND target_language = ?"
        cursor = self.execute_query(query, (source_lang, target_lang))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
        
        return None
    
    def find_by_source_language(self, source_lang: str) -> List[LanguagePair]:
        """Find all language pairs with specific source language.
        
        Args:
            source_lang: Source language code
            
        Returns:
            List[LanguagePair]: List of language pairs
        """
        return self.find_by_field('source_language', source_lang)
    
    def find_by_target_language(self, target_lang: str) -> List[LanguagePair]:
        """Find all language pairs with specific target language.
        
        Args:
            target_lang: Target language code
            
        Returns:
            List[LanguagePair]: List of language pairs
        """
        return self.find_by_field('target_language', target_lang)
    
    def get_or_create(self, source_lang: str, target_lang: str) -> Optional[LanguagePair]:
        """Get existing language pair or create new one.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Optional[LanguagePair]: Language pair or None if creation failed
        """
        # Try to find existing pair
        existing_pair = self.find_by_languages(source_lang, target_lang)
        if existing_pair:
            return existing_pair
        
        # Create new pair
        new_pair = LanguagePair(
            source_language=source_lang,
            target_language=target_lang
        )
        
        if new_pair.is_valid():
            return self.create(new_pair)
        
        return None
    
    def get_available_pairs_for_translator(self, translator_id: int) -> List[LanguagePair]:
        """Get language pairs that have rates defined for a translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[LanguagePair]: Available language pairs
        """
        query = """
        SELECT DISTINCT lp.*
        FROM language_pairs lp
        JOIN translator_rates tr ON lp.id = tr.language_pair_id
        WHERE tr.translator_id = ?
        ORDER BY lp.source_language, lp.target_language
        """
        
        cursor = self.execute_query(query, (translator_id,))
        pairs = []
        
        if cursor:
            for row in cursor.fetchall():
                pair = self._row_to_model(row)
                pairs.append(pair)
        
        return pairs


class MatchCategoryRepository:
    """Repository for match category reference data."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all match categories with their IDs.
        
        Returns:
            List[Dict[str, Any]]: Match categories with database IDs
        """
        query = "SELECT * FROM match_categories ORDER BY display_order"
        cursor = self.db_manager.execute_query(query)
        categories = []
        
        if cursor:
            for row in cursor.fetchall():
                categories.append({
                    'id': row['id'],
                    'name': row['name'],
                    'display_order': row['display_order']
                })
        
        return categories
    
    def get_category_id(self, category_name: str) -> Optional[int]:
        """Get database ID for a match category.
        
        Args:
            category_name: Category name
            
        Returns:
            Optional[int]: Category ID or None
        """
        query = "SELECT id FROM match_categories WHERE name = ?"
        cursor = self.db_manager.execute_query(query, (category_name,))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return row['id']
        
        return None
    
    def get_category_name(self, category_id: int) -> Optional[str]:
        """Get category name by ID.
        
        Args:
            category_id: Category ID
            
        Returns:
            Optional[str]: Category name or None
        """
        query = "SELECT name FROM match_categories WHERE id = ?"
        cursor = self.db_manager.execute_query(query, (category_id,))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return row['name']
        
        return None
    
    def get_category_mapping(self) -> Dict[str, int]:
        """Get mapping from category names to IDs.
        
        Returns:
            Dict[str, int]: Category name to ID mapping
        """
        categories = self.get_all_categories()
        return {cat['name']: cat['id'] for cat in categories}
    
    def ensure_default_categories(self) -> bool:
        """Ensure all default match categories exist in database.
        
        Returns:
            bool: True if successful
        """
        try:
            default_categories = [
                ('Context Match', 1),
                ('Repetitions', 2),
                ('100%', 3),
                ('95% - 99%', 4),
                ('85% - 94%', 5),
                ('75% - 84%', 6),
                ('50% - 74%', 7),
                ('No Match', 8),
                ('MT Match', 9)
            ]
            
            operations = []
            for name, order in default_categories:
                # Check if category exists
                existing_id = self.get_category_id(name)
                if not existing_id:
                    query = "INSERT INTO match_categories (name, display_order) VALUES (?, ?)"
                    operations.append((query, (name, order)))
            
            if operations:
                return self.db_manager.execute_transaction(operations)
            
            return True  # No operations needed
            
        except Exception as e:
            self.logger.error(f"Error ensuring default categories: {e}")
            return False