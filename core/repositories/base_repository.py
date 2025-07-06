"""
Translation Cost Calculator - Base Repository

Abstract base repository providing common database operations and patterns.
Implements the Repository pattern with clean separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
import sqlite3
import logging
from dataclasses import asdict

from config.database import DatabaseManager

# Generic type for domain models
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for all data access objects."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection from manager.
        
        Returns:
            Optional[sqlite3.Connection]: Database connection or None
        """
        return self.db_manager.get_connection()
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Get the primary table name for this repository.
        
        Returns:
            str: Table name
        """
        pass
    
    @abstractmethod
    def _row_to_model(self, row: sqlite3.Row) -> T:
        """Convert database row to domain model.
        
        Args:
            row: Database row from query
            
        Returns:
            T: Domain model instance
        """
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert domain model to dictionary for database operations.
        
        Args:
            model: Domain model instance
            
        Returns:
            Dict[str, Any]: Model data as dictionary
        """
        pass
    
    def execute_query(self, query: str, parameters: Optional[tuple] = None) -> Optional[sqlite3.Cursor]:
        """Execute a database query with error handling.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            Optional[sqlite3.Cursor]: Query cursor or None if failed
        """
        try:
            cursor = self.db_manager.execute_query(query, parameters)
            if cursor is None:
                self.logger.error(f"Query execution failed: {query}")
            return cursor
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            return None
    
    def execute_transaction(self, operations: List[tuple[str, Optional[tuple]]]) -> bool:
        """Execute multiple operations in a transaction.
        
        Args:
            operations: List of (query, parameters) tuples
            
        Returns:
            bool: True if transaction successful
        """
        try:
            return self.db_manager.execute_transaction(operations)
        except Exception as e:
            self.logger.error(f"Transaction execution error: {e}")
            return False
    
    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Optional[T]: Entity instance or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        cursor = self.execute_query(query, (id,))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
        
        return None
    
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Find all entities with optional pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List[T]: List of entity instances
        """
        query = f"SELECT * FROM {self.table_name}"
        parameters = None
        
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = self.execute_query(query, parameters)
        entities = []
        
        if cursor:
            for row in cursor.fetchall():
                try:
                    entity = self._row_to_model(row)
                    entities.append(entity)
                except Exception as e:
                    self.logger.error(f"Error converting row to model: {e}")
        
        return entities
    
    def count_all(self) -> int:
        """Count total number of entities.
        
        Returns:
            int: Total count
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        cursor = self.execute_query(query)
        
        if cursor:
            result = cursor.fetchone()
            return result[0] if result else 0
        
        return 0
    
    def exists_by_id(self, id: int) -> bool:
        """Check if entity exists by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            bool: True if entity exists
        """
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1"
        cursor = self.execute_query(query, (id,))
        
        if cursor:
            return cursor.fetchone() is not None
        
        return False
    
    def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID.
        
        Args:
            id: Entity ID to delete
            
        Returns:
            bool: True if deletion successful
        """
        if not self.exists_by_id(id):
            self.logger.warning(f"Cannot delete {self.table_name} with id {id}: not found")
            return False
        
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        cursor = self.execute_query(query, (id,))
        
        if cursor and cursor.rowcount > 0:
            self.logger.info(f"Deleted {self.table_name} with id {id}")
            return True
        
        self.logger.error(f"Failed to delete {self.table_name} with id {id}")
        return False
    
    def create(self, model: T) -> Optional[T]:
        """Create new entity in database.
        
        Args:
            model: Entity instance to create
            
        Returns:
            Optional[T]: Created entity with ID or None if failed
        """
        try:
            data = self._model_to_dict(model)
            
            # Remove id field for insert
            if 'id' in data:
                del data['id']
            
            # Build INSERT query
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [data[col] for col in columns]
            
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor = self.execute_query(query, tuple(values))
            
            if cursor and cursor.lastrowid:
                # Return the created entity with new ID
                return self.find_by_id(cursor.lastrowid)
            
            self.logger.error(f"Failed to create {self.table_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating {self.table_name}: {e}")
            return None
    
    def update(self, model: T) -> Optional[T]:
        """Update existing entity in database.
        
        Args:
            model: Entity instance to update
            
        Returns:
            Optional[T]: Updated entity or None if failed
        """
        try:
            data = self._model_to_dict(model)
            entity_id = data.get('id')
            
            if not entity_id:
                self.logger.error(f"Cannot update {self.table_name}: no ID provided")
                return None
            
            if not self.exists_by_id(entity_id):
                self.logger.error(f"Cannot update {self.table_name}: id {entity_id} not found")
                return None
            
            # Remove id from update data
            update_data = {k: v for k, v in data.items() if k != 'id'}
            
            if not update_data:
                self.logger.warning(f"No data to update for {self.table_name} id {entity_id}")
                return self.find_by_id(entity_id)
            
            # Build UPDATE query
            set_clause = ', '.join([f"{col} = ?" for col in update_data.keys()])
            values = list(update_data.values()) + [entity_id]
            
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            cursor = self.execute_query(query, tuple(values))
            
            if cursor and cursor.rowcount > 0:
                self.logger.info(f"Updated {self.table_name} with id {entity_id}")
                return self.find_by_id(entity_id)
            
            self.logger.error(f"Failed to update {self.table_name} with id {entity_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating {self.table_name}: {e}")
            return None
    
    def save(self, model: T) -> Optional[T]:
        """Save entity (create or update based on ID).
        
        Args:
            model: Entity instance to save
            
        Returns:
            Optional[T]: Saved entity or None if failed
        """
        data = self._model_to_dict(model)
        entity_id = data.get('id')
        
        if entity_id and self.exists_by_id(entity_id):
            return self.update(model)
        else:
            return self.create(model)
    
    def find_by_field(self, field_name: str, field_value: Any) -> List[T]:
        """Find entities by a specific field value.
        
        Args:
            field_name: Field name to search
            field_value: Value to search for
            
        Returns:
            List[T]: List of matching entities
        """
        query = f"SELECT * FROM {self.table_name} WHERE {field_name} = ?"
        cursor = self.execute_query(query, (field_value,))
        entities = []
        
        if cursor:
            for row in cursor.fetchall():
                try:
                    entity = self._row_to_model(row)
                    entities.append(entity)
                except Exception as e:
                    self.logger.error(f"Error converting row to model: {e}")
        
        return entities
    
    def find_one_by_field(self, field_name: str, field_value: Any) -> Optional[T]:
        """Find single entity by field value.
        
        Args:
            field_name: Field name to search
            field_value: Value to search for
            
        Returns:
            Optional[T]: First matching entity or None
        """
        entities = self.find_by_field(field_name, field_value)
        return entities[0] if entities else None
    
    def execute_custom_query(self, query: str, parameters: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute custom query and return results as dictionaries.
        
        Args:
            query: Custom SQL query
            parameters: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        cursor = self.execute_query(query, parameters)
        results = []
        
        if cursor:
            columns = [description[0] for description in cursor.description]
            for row in cursor.fetchall():
                result_dict = dict(zip(columns, row))
                results.append(result_dict)
        
        return results
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get table information and statistics.
        
        Returns:
            Dict[str, Any]: Table information
        """
        info = {
            'table_name': self.table_name,
            'row_count': self.count_all(),
            'columns': [],
            'indexes': []
        }
        
        # Get column information
        cursor = self.execute_query(f"PRAGMA table_info({self.table_name})")
        if cursor:
            info['columns'] = [
                {
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default_value': row[4],
                    'primary_key': bool(row[5])
                }
                for row in cursor.fetchall()
            ]
        
        # Get index information
        cursor = self.execute_query(f"PRAGMA index_list({self.table_name})")
        if cursor:
            info['indexes'] = [
                {
                    'name': row[1],
                    'unique': bool(row[2])
                }
                for row in cursor.fetchall()
            ]
        
        return info


class RepositoryError(Exception):
    """Custom exception for repository operations."""
    
    def __init__(self, message: str, operation: str = "", entity_id: Optional[int] = None):
        """Initialize repository error.
        
        Args:
            message: Error message
            operation: Operation that failed
            entity_id: Entity ID if applicable
        """
        self.message = message
        self.operation = operation
        self.entity_id = entity_id
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.entity_id:
            parts.append(f"Entity ID: {self.entity_id}")
        return " | ".join(parts)