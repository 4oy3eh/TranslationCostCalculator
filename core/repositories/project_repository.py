"""
Translation Cost Calculator - Project Repository

Data access layer for Project and ProjectFile entities with specialized queries
for project management and file handling.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from core.repositories.base_repository import BaseRepository, RepositoryError
from core.models.project import Project, ProjectFile
from core.models.analysis import FileAnalysisData, ProjectAnalysisData
from config.database import DatabaseManager


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "projects"
    
    def _row_to_model(self, row: sqlite3.Row) -> Project:
        """Convert database row to Project model.
        
        Args:
            row: Database row
            
        Returns:
            Project: Project domain model
        """
        project = Project()
        project.id = row['id']
        project.name = row['name']
        project.translator_id = row['translator_id']
        project.client_id = row['client_id']
        project.language_pair_id = row['language_pair_id']
        project.mt_percentage = row['mt_percentage']
        
        # Parse datetime fields
        if row['created_at']:
            project.created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            project.updated_at = datetime.fromisoformat(row['updated_at'])
        
        # Set language codes from language pair (requires join)
        # Will be populated by specialized queries
        project.source_language = ""
        project.target_language = ""
        
        return project
    
    def _model_to_dict(self, model: Project) -> Dict[str, Any]:
        """Convert Project model to dictionary for database operations.
        
        Args:
            model: Project model
            
        Returns:
            Dict[str, Any]: Project data dictionary
        """
        data = {
            'id': model.id,
            'name': model.name,
            'translator_id': model.translator_id,
            'client_id': model.client_id,
            'language_pair_id': model.language_pair_id,
            'mt_percentage': model.mt_percentage
        }
        
        # Add timestamps if present
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
        
        return data
    
    def find_by_translator_id(self, translator_id: int) -> List[Project]:
        """Find all projects for a specific translator.
        
        Args:
            translator_id: Translator ID
            
        Returns:
            List[Project]: List of projects
        """
        query = """
        SELECT p.*, lp.source_language, lp.target_language
        FROM projects p
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        WHERE p.translator_id = ?
        ORDER BY p.created_at DESC
        """
        
        cursor = self.execute_query(query, (translator_id,))
        projects = []
        
        if cursor:
            for row in cursor.fetchall():
                project = self._row_to_model(row)
                project.source_language = row['source_language']
                project.target_language = row['target_language']
                projects.append(project)
        
        return projects
    
    def find_by_client_id(self, client_id: int) -> List[Project]:
        """Find all projects for a specific client.
        
        Args:
            client_id: Client ID
            
        Returns:
            List[Project]: List of projects
        """
        query = """
        SELECT p.*, lp.source_language, lp.target_language
        FROM projects p
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        WHERE p.client_id = ?
        ORDER BY p.created_at DESC
        """
        
        cursor = self.execute_query(query, (client_id,))
        projects = []
        
        if cursor:
            for row in cursor.fetchall():
                project = self._row_to_model(row)
                project.source_language = row['source_language']
                project.target_language = row['target_language']
                projects.append(project)
        
        return projects
    
    def find_with_details(self, project_id: int) -> Optional[Project]:
        """Find project with complete details including language information.
        
        Args:
            project_id: Project ID
            
        Returns:
            Optional[Project]: Project with complete details or None
        """
        query = """
        SELECT p.*, lp.source_language, lp.target_language,
               t.name as translator_name, c.name as client_name
        FROM projects p
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        JOIN translators t ON p.translator_id = t.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE p.id = ?
        """
        
        cursor = self.execute_query(query, (project_id,))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                project = self._row_to_model(row)
                project.source_language = row['source_language']
                project.target_language = row['target_language']
                return project
        
        return None
    
    def find_by_language_pair(self, source_lang: str, target_lang: str) -> List[Project]:
        """Find projects by language pair.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List[Project]: List of projects
        """
        query = """
        SELECT p.*, lp.source_language, lp.target_language
        FROM projects p
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        WHERE lp.source_language = ? AND lp.target_language = ?
        ORDER BY p.created_at DESC
        """
        
        cursor = self.execute_query(query, (source_lang, target_lang))
        projects = []
        
        if cursor:
            for row in cursor.fetchall():
                project = self._row_to_model(row)
                project.source_language = row['source_language']
                project.target_language = row['target_language']
                projects.append(project)
        
        return projects
    
    def get_project_summary(self) -> List[Dict[str, Any]]:
        """Get project summary with statistics.
        
        Returns:
            List[Dict[str, Any]]: Project summaries
        """
        query = """
        SELECT p.id, p.name, p.created_at, p.mt_percentage,
               t.name as translator_name,
               c.name as client_name,
               lp.source_language, lp.target_language,
               COUNT(pf.id) as file_count
        FROM projects p
        JOIN translators t ON p.translator_id = t.id
        LEFT JOIN clients c ON p.client_id = c.id
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        LEFT JOIN project_files pf ON p.id = pf.project_id
        GROUP BY p.id, p.name, p.created_at, p.mt_percentage,
                 t.name, c.name, lp.source_language, lp.target_language
        ORDER BY p.created_at DESC
        """
        
        return self.execute_custom_query(query)
    
    def search_projects(self, search_term: str) -> List[Project]:
        """Search projects by name, translator, or client.
        
        Args:
            search_term: Search term
            
        Returns:
            List[Project]: Matching projects
        """
        search_pattern = f"%{search_term}%"
        query = """
        SELECT p.*, lp.source_language, lp.target_language
        FROM projects p
        JOIN language_pairs lp ON p.language_pair_id = lp.id
        JOIN translators t ON p.translator_id = t.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE p.name LIKE ? OR t.name LIKE ? OR c.name LIKE ?
        ORDER BY p.created_at DESC
        """
        
        cursor = self.execute_query(query, (search_pattern, search_pattern, search_pattern))
        projects = []
        
        if cursor:
            for row in cursor.fetchall():
                project = self._row_to_model(row)
                project.source_language = row['source_language']
                project.target_language = row['target_language']
                projects.append(project)
        
        return projects
    
    def create_with_language_pair(self, project: Project, source_lang: str, target_lang: str) -> Optional[Project]:
        """Create project with language pair resolution.
        
        Args:
            project: Project to create
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Optional[Project]: Created project or None
        """
        # First, find or create language pair
        language_pair_id = self._get_or_create_language_pair(source_lang, target_lang)
        if not language_pair_id:
            self.logger.error(f"Failed to create language pair {source_lang}>{target_lang}")
            return None
        
        # Set language pair ID and create project
        project.language_pair_id = language_pair_id
        project.source_language = source_lang
        project.target_language = target_lang
        
        return self.create(project)
    
    def _get_or_create_language_pair(self, source_lang: str, target_lang: str) -> Optional[int]:
        """Get or create language pair and return its ID.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Optional[int]: Language pair ID or None
        """
        # Try to find existing language pair
        query = "SELECT id FROM language_pairs WHERE source_language = ? AND target_language = ?"
        cursor = self.execute_query(query, (source_lang, target_lang))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return row['id']
        
        # Create new language pair
        insert_query = "INSERT INTO language_pairs (source_language, target_language) VALUES (?, ?)"
        cursor = self.execute_query(insert_query, (source_lang, target_lang))
        
        if cursor and cursor.lastrowid:
            return cursor.lastrowid
        
        return None


class ProjectFileRepository(BaseRepository[ProjectFile]):
    """Repository for ProjectFile entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    @property
    def table_name(self) -> str:
        return "project_files"
    
    def _row_to_model(self, row: sqlite3.Row) -> ProjectFile:
        """Convert database row to ProjectFile model.
        
        Args:
            row: Database row
            
        Returns:
            ProjectFile: ProjectFile domain model
        """
        file_obj = ProjectFile()
        file_obj.id = row['id']
        file_obj.project_id = row['project_id']
        file_obj.filename = row['filename']
        file_obj.file_path = row['file_path']
        file_obj.parsed_data = row['parsed_data']
        
        if row['created_at']:
            file_obj.created_at = datetime.fromisoformat(row['created_at'])
        
        return file_obj
    
    def _model_to_dict(self, model: ProjectFile) -> Dict[str, Any]:
        """Convert ProjectFile model to dictionary.
        
        Args:
            model: ProjectFile model
            
        Returns:
            Dict[str, Any]: File data dictionary
        """
        data = {
            'id': model.id,
            'project_id': model.project_id,
            'filename': model.filename,
            'file_path': model.file_path,
            'parsed_data': model.parsed_data
        }
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        
        return data
    
    def find_by_project_id(self, project_id: int) -> List[ProjectFile]:
        """Find all files for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List[ProjectFile]: List of project files
        """
        return self.find_by_field('project_id', project_id)
    
    def find_by_filename(self, project_id: int, filename: str) -> Optional[ProjectFile]:
        """Find file by project ID and filename.
        
        Args:
            project_id: Project ID
            filename: Filename to search for
            
        Returns:
            Optional[ProjectFile]: Project file or None
        """
        query = "SELECT * FROM project_files WHERE project_id = ? AND filename = ?"
        cursor = self.execute_query(query, (project_id, filename))
        
        if cursor:
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
        
        return None
    
    def create_with_analysis_data(self, project_id: int, filename: str, 
                                  file_path: str, analysis_data: FileAnalysisData) -> Optional[ProjectFile]:
        """Create project file with analysis data.
        
        Args:
            project_id: Project ID
            filename: Filename
            file_path: File path
            analysis_data: Analysis data to serialize
            
        Returns:
            Optional[ProjectFile]: Created project file or None
        """
        try:
            # Serialize analysis data to JSON
            parsed_data = json.dumps(analysis_data.to_dict())
            
            # Create project file
            project_file = ProjectFile(
                project_id=project_id,
                filename=filename,
                file_path=file_path,
                parsed_data=parsed_data
            )
            
            return self.create(project_file)
            
        except Exception as e:
            self.logger.error(f"Error creating project file with analysis data: {e}")
            return None
    
    def get_analysis_data(self, file_id: int) -> Optional[FileAnalysisData]:
        """Get analysis data for a project file.
        
        Args:
            file_id: Project file ID
            
        Returns:
            Optional[FileAnalysisData]: Analysis data or None
        """
        project_file = self.find_by_id(file_id)
        if not project_file:
            return None
        
        try:
            # Parse JSON data back to FileAnalysisData
            data_dict = json.loads(project_file.parsed_data)
            return FileAnalysisData.from_dict(data_dict)
            
        except Exception as e:
            self.logger.error(f"Error parsing analysis data for file {file_id}: {e}")
            return None
    
    def delete_by_project_id(self, project_id: int) -> bool:
        """Delete all files for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            bool: True if deletion successful
        """
        query = "DELETE FROM project_files WHERE project_id = ?"
        cursor = self.execute_query(query, (project_id,))
        
        if cursor:
            self.logger.info(f"Deleted {cursor.rowcount} files for project {project_id}")
            return True
        
        return False
    
    def get_project_file_summary(self, project_id: int) -> List[Dict[str, Any]]:
        """Get summary of files for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List[Dict[str, Any]]: File summaries
        """
        query = """
        SELECT id, filename, file_path, file_size, cat_tool, created_at
        FROM project_files
        WHERE project_id = ?
        ORDER BY created_at ASC
        """
        
        return self.execute_custom_query(query, (project_id,))