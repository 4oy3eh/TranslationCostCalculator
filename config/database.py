"""
Translation Cost Calculator - Database Configuration

Database connection management, initialization, and migration handling.
Provides centralized database access for the application.
"""

import sqlite3
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from config.settings import Settings


class DatabaseManager:
    """Manages database connections, initialization, and migrations."""
    
    def __init__(self):
        """Initialize database manager."""
        self.connection: Optional[sqlite3.Connection] = None
        self.database_path = Settings.DATABASE_FILE
        self.migrations_dir = Settings.MIGRATIONS_DIR
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """Initialize database connection and run migrations.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create database connection
            if not self._create_connection():
                return False
            
            # Run migrations if needed
            if not self._run_migrations():
                return False
                
            self.logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
    
    def _create_connection(self) -> bool:
        """Create SQLite database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Ensure data directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection with configuration
            self.connection = sqlite3.connect(
                str(self.database_path),
                timeout=Settings.DATABASE_CONFIG["timeout"],
                check_same_thread=Settings.DATABASE_CONFIG["check_same_thread"],
                isolation_level=Settings.DATABASE_CONFIG["isolation_level"]
            )
            
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Set row factory for dictionary-like access
            self.connection.row_factory = sqlite3.Row
            
            self.logger.info(f"Database connection established: {self.database_path}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create database connection: {e}")
            return False
    
    def _run_migrations(self) -> bool:
        """Run database migrations if needed.
        
        Returns:
            bool: True if migrations successful, False otherwise
        """
        try:
            # Create migration tracking table if it doesn't exist
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL UNIQUE,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            
            # Check if initial migration has been applied
            cursor.execute("SELECT version FROM schema_migrations WHERE version = ?", ('001_initial',))
            result = cursor.fetchone()
            
            if not result:
                # Run initial migration
                return self._apply_initial_migration()
            
            self.logger.info("Database migrations up to date")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Migration execution failed: {e}")
            return False
    
    def _apply_initial_migration(self) -> bool:
        """Apply the initial database migration.
        
        Returns:
            bool: True if migration successful
        """
        try:
            migration_path = self.migrations_dir / "001_initial.sql"
            
            if not migration_path.exists():
                self.logger.error(f"Initial migration file not found: {migration_path}")
                return False
            
            # Read migration SQL
            with open(migration_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Parse SQL statements with proper ordering
            statements = self._parse_sql_statements(migration_sql)
            
            if not statements:
                self.logger.error("No valid SQL statements found in migration")
                return False
            
            # Execute statements in transaction
            cursor = self.connection.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                for i, statement in enumerate(statements):
                    self.logger.debug(f"Executing statement {i+1}: {statement[:50]}...")
                    cursor.execute(statement)
                
                # Record migration
                cursor.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    ('001_initial', 'Initial database schema with all core tables and relationships')
                )
                
                self.connection.commit()
                self.logger.info("Initial migration applied successfully")
                return True
                
            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"Failed to execute migration statement: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to apply initial migration: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _parse_sql_statements(self, sql_content: str) -> List[str]:
        """Parse SQL content into properly ordered statements.
        
        Args:
            sql_content: Raw SQL content from migration file
            
        Returns:
            List[str]: Ordered list of SQL statements
        """
        # Remove SQL comments but preserve structure
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                lines.append(line)  # Keep original line with indentation
        
        # Join lines preserving newlines for triggers
        clean_sql = '\n'.join(lines)
        
        # Split by semicolon, but handle triggers specially
        statements = []
        current_statement = ""
        in_trigger = False
        
        for line in clean_sql.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for trigger start
            if line.upper().startswith('CREATE TRIGGER'):
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = line + '\n'
                in_trigger = True
                continue
            
            # If in trigger, accumulate until END;
            if in_trigger:
                current_statement += line + '\n'
                if line.upper() == 'END;':
                    statements.append(current_statement.strip())
                    current_statement = ""
                    in_trigger = False
                continue
            
            # Regular statement handling
            current_statement += line + ' '
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add final statement if exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Filter and clean statements
        cleaned_statements = []
        for stmt in statements:
            if stmt and not stmt.upper().startswith('PRAGMA') and len(stmt) > 5:
                cleaned_statements.append(stmt)
        
        # Order statements properly
        ordered_statements = self._order_sql_statements(cleaned_statements)
        
        self.logger.debug(f"Parsed {len(ordered_statements)} SQL statements from migration")
        return ordered_statements
    
    def _order_sql_statements(self, statements: List[str]) -> List[str]:
        """Order SQL statements in correct execution order.
        
        Args:
            statements: List of SQL statements
            
        Returns:
            List[str]: Properly ordered statements
        """
        create_tables = []
        create_indexes = []
        create_triggers = []
        insert_statements = []
        other_statements = []
        
        for stmt in statements:
            stmt_upper = stmt.upper().strip()
            
            if stmt_upper.startswith('CREATE TABLE'):
                create_tables.append(stmt)
            elif stmt_upper.startswith('CREATE INDEX'):
                create_indexes.append(stmt)
            elif stmt_upper.startswith('CREATE TRIGGER'):
                create_triggers.append(stmt)
            elif stmt_upper.startswith('INSERT'):
                insert_statements.append(stmt)
            else:
                other_statements.append(stmt)
        
        # Order: Tables -> Other -> Indexes -> Triggers -> Inserts
        ordered = []
        ordered.extend(create_tables)
        ordered.extend(other_statements)
        ordered.extend(create_indexes)
        ordered.extend(create_triggers)
        ordered.extend(insert_statements)
        
        self.logger.debug(f"Statement ordering: {len(create_tables)} tables, "
                         f"{len(create_indexes)} indexes, {len(create_triggers)} triggers, "
                         f"{len(insert_statements)} inserts, {len(other_statements)} other")
        
        return ordered
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Get the current database connection.
        
        Returns:
            Optional[sqlite3.Connection]: Database connection or None if not initialized
        """
        return self.connection
    
    def execute_query(self, query: str, parameters: Optional[tuple] = None) -> Optional[sqlite3.Cursor]:
        """Execute a database query.
        
        Args:
            query: SQL query string
            parameters: Query parameters tuple
            
        Returns:
            Optional[sqlite3.Cursor]: Query cursor or None if failed
        """
        try:
            if not self.connection:
                self.logger.error("No database connection available")
                return None
            
            cursor = self.connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            return cursor
            
        except sqlite3.Error as e:
            self.logger.error(f"Query execution failed: {e}")
            return None
    
    def execute_transaction(self, queries: list[tuple[str, Optional[tuple]]]) -> bool:
        """Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, parameters) tuples
            
        Returns:
            bool: True if transaction successful, False otherwise
        """
        try:
            if not self.connection:
                self.logger.error("No database connection available")
                return False
            
            cursor = self.connection.cursor()
            
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Execute all queries
            for query, parameters in queries:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
            
            # Commit transaction
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Transaction failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def close(self) -> None:
        """Close database connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.logger.info("Database connection closed")
                
        except sqlite3.Error as e:
            self.logger.error(f"Error closing database connection: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics.
        
        Returns:
            Dict[str, Any]: Database information
        """
        info = {
            "database_path": str(self.database_path),
            "database_exists": self.database_path.exists(),
            "connection_active": self.connection is not None,
            "size_bytes": 0,
            "tables": []
        }
        
        try:
            if self.database_path.exists():
                info["size_bytes"] = self.database_path.stat().st_size
            
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info["tables"] = [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
        
        return info
    
    def backup_database(self, backup_path: Path) -> bool:
        """Create a backup of the database.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            if not self.connection:
                self.logger.error("No database connection for backup")
                return False
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup connection
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Perform backup
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            self.logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()