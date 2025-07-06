"""
Translation Cost Calculator - Project Service

Business logic for project creation, management, and file handling.
Coordinates between parsers, repositories, and calculation services.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.models.project import Project, ProjectFile
from core.models.analysis import FileAnalysisData, ProjectAnalysisData
from core.models.translator import Translator, Client
from core.repositories.project_repository import ProjectRepository, ProjectFileRepository
from core.repositories.translator_repository import TranslatorRepository, ClientRepository
from core.repositories.rate_repository import LanguagePairRepository
from parsers.parser_factory import get_parser_factory, ParserFactory
from utils.validation import ValidationResult, validate_input, validate_file
from utils.file_utils import FileUtils, get_temp_manager
from config.database import DatabaseManager


class ProjectService:
    """Service for project management and file processing."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize project service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.project_repository = ProjectRepository(db_manager)
        self.project_file_repository = ProjectFileRepository(db_manager)
        self.translator_repository = TranslatorRepository(db_manager)
        self.client_repository = ClientRepository(db_manager)
        self.language_pair_repository = LanguagePairRepository(db_manager)
        self.parser_factory = get_parser_factory()
        self.temp_manager = get_temp_manager()
        self.logger = logging.getLogger(__name__)
    
    def create_project(self, name: str, translator_id: int, 
                      source_language: str, target_language: str,
                      client_id: Optional[int] = None, 
                      mt_percentage: int = 70) -> Tuple[Optional[Project], ValidationResult]:
        """Create a new project.
        
        Args:
            name: Project name
            translator_id: Translator ID
            source_language: Source language code
            target_language: Target language code
            client_id: Optional client ID
            mt_percentage: MT percentage for 100% matches
            
        Returns:
            Tuple[Optional[Project], ValidationResult]: Created project and validation result
        """
        # Validate inputs
        validation = self._validate_project_creation(
            name, translator_id, source_language, target_language, client_id, mt_percentage
        )
        
        if not validation.is_valid:
            return None, validation
        
        try:
            # Create project instance
            project = Project(
                name=name.strip(),
                translator_id=translator_id,
                client_id=client_id,
                source_language=source_language.strip().lower(),
                target_language=target_language.strip().lower(),
                mt_percentage=mt_percentage
            )
            
            # Create in database with language pair resolution
            created_project = self.project_repository.create_with_language_pair(
                project, project.source_language, project.target_language
            )
            
            if created_project:
                self.logger.info(f"Created project: {created_project.name} (ID: {created_project.id})")
                return created_project, validation
            else:
                validation.add_error("Failed to create project in database")
                return None, validation
                
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            validation.add_error(f"Project creation failed: {e}")
            return None, validation
    
    def load_project(self, project_id: int, load_files: bool = True) -> Optional[Project]:
        """Load project with optional file data.
        
        Args:
            project_id: Project ID to load
            load_files: Whether to load file analysis data
            
        Returns:
            Optional[Project]: Loaded project or None if not found
        """
        try:
            # Load project with details
            project = self.project_repository.find_with_details(project_id)
            
            if not project:
                self.logger.error(f"Project not found: {project_id}")
                return None
            
            if load_files:
                # Load and parse file data
                project_analysis = self._load_project_analysis_data(project_id)
                if project_analysis:
                    project.update_analysis_data(project_analysis)
            
            return project
            
        except Exception as e:
            self.logger.error(f"Error loading project {project_id}: {e}")
            return None
    
    def add_file_to_project(self, project_id: int, 
                           file_path: Path) -> Tuple[Optional[FileAnalysisData], ValidationResult]:
        """Add a file to an existing project.
        
        Args:
            project_id: Project ID
            file_path: Path to file to add
            
        Returns:
            Tuple[Optional[FileAnalysisData], ValidationResult]: Analysis data and validation result
        """
        # Validate file
        file_validation = validate_file(file_path)
        if not file_validation.is_valid:
            return None, file_validation
        
        try:
            # Load project to get language information
            project = self.project_repository.find_by_id(project_id)
            if not project:
                file_validation.add_error("Project not found")
                return None, file_validation
            
            # Parse file
            analysis_data = self.parser_factory.parse_file(file_path)
            if not analysis_data:
                file_validation.add_error("Failed to parse file")
                return None, file_validation
            
            # Validate language consistency
            if project.source_language and project.target_language:
                if (analysis_data.source_language != project.source_language or
                    analysis_data.target_language != project.target_language):
                    file_validation.add_warning(
                        f"File language pair ({analysis_data.get_language_pair_code()}) "
                        f"differs from project ({project.get_language_pair_code()})"
                    )
            
            # Save file to project
            project_file = self.project_file_repository.create_with_analysis_data(
                project_id, analysis_data.filename, str(file_path), analysis_data
            )
            
            if project_file:
                self.logger.info(f"Added file to project {project_id}: {analysis_data.filename}")
                return analysis_data, file_validation
            else:
                file_validation.add_error("Failed to save file to project")
                return None, file_validation
                
        except Exception as e:
            self.logger.error(f"Error adding file to project {project_id}: {e}")
            file_validation.add_error(f"Error processing file: {e}")
            return None, file_validation
    
    def remove_file_from_project(self, project_id: int, file_id: int) -> bool:
        """Remove a file from a project.
        
        Args:
            project_id: Project ID
            file_id: File ID to remove
            
        Returns:
            bool: True if removal successful
        """
        try:
            # Verify file belongs to project
            project_file = self.project_file_repository.find_by_id(file_id)
            if not project_file or project_file.project_id != project_id:
                self.logger.error(f"File {file_id} not found in project {project_id}")
                return False
            
            # Delete file
            success = self.project_file_repository.delete_by_id(file_id)
            if success:
                self.logger.info(f"Removed file {file_id} from project {project_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error removing file {file_id} from project {project_id}: {e}")
            return False
    
    def update_project(self, project: Project) -> Tuple[Optional[Project], ValidationResult]:
        """Update an existing project.
        
        Args:
            project: Project with updated data
            
        Returns:
            Tuple[Optional[Project], ValidationResult]: Updated project and validation result
        """
        # Validate project data
        validation = ValidationResult()
        
        if not project.id:
            validation.add_error("Project ID is required for update")
            return None, validation
        
        name_validation = validate_input('project_name', project.name)
        validation = validation.merge(name_validation)
        
        if project.mt_percentage < 0 or project.mt_percentage > 100:
            validation.add_error("MT percentage must be between 0 and 100")
        
        if not validation.is_valid:
            return None, validation
        
        try:
            # Update in database
            updated_project = self.project_repository.update(project)
            
            if updated_project:
                self.logger.info(f"Updated project: {updated_project.name} (ID: {updated_project.id})")
                return updated_project, validation
            else:
                validation.add_error("Failed to update project in database")
                return None, validation
                
        except Exception as e:
            self.logger.error(f"Error updating project: {e}")
            validation.add_error(f"Project update failed: {e}")
            return None, validation
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its files.
        
        Args:
            project_id: Project ID to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            # First delete all project files
            self.project_file_repository.delete_by_project_id(project_id)
            
            # Then delete the project
            success = self.project_repository.delete_by_id(project_id)
            
            if success:
                self.logger.info(f"Deleted project {project_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    def get_project_list(self, translator_id: Optional[int] = None,
                        client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of projects with summary information.
        
        Args:
            translator_id: Optional filter by translator ID
            client_id: Optional filter by client ID
            
        Returns:
            List[Dict[str, Any]]: List of project summaries
        """
        try:
            if translator_id:
                projects = self.project_repository.find_by_translator_id(translator_id)
            elif client_id:
                projects = self.project_repository.find_by_client_id(client_id)
            else:
                projects = self.project_repository.find_all()
            
            # Convert to summary format
            project_summaries = []
            for project in projects:
                summary = project.to_dict()
                
                # Add file count
                files = self.project_file_repository.find_by_project_id(project.id)
                summary['file_count'] = len(files)
                
                project_summaries.append(summary)
            
            return project_summaries
            
        except Exception as e:
            self.logger.error(f"Error getting project list: {e}")
            return []
    
    def search_projects(self, search_term: str) -> List[Dict[str, Any]]:
        """Search projects by name or associated entities.
        
        Args:
            search_term: Search term
            
        Returns:
            List[Dict[str, Any]]: Matching project summaries
        """
        try:
            projects = self.project_repository.search_projects(search_term)
            
            # Convert to summary format
            project_summaries = []
            for project in projects:
                summary = project.to_dict()
                
                # Add file count
                files = self.project_file_repository.find_by_project_id(project.id)
                summary['file_count'] = len(files)
                
                project_summaries.append(summary)
            
            return project_summaries
            
        except Exception as e:
            self.logger.error(f"Error searching projects: {e}")
            return []
    
    def get_project_files(self, project_id: int) -> List[Dict[str, Any]]:
        """Get list of files in a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List[Dict[str, Any]]: List of file information
        """
        try:
            project_files = self.project_file_repository.find_by_project_id(project_id)
            
            file_list = []
            for project_file in project_files:
                # Parse analysis data to get summary
                try:
                    analysis_data = self.project_file_repository.get_analysis_data(project_file.id)
                    if analysis_data:
                        file_info = {
                            'id': project_file.id,
                            'filename': project_file.filename,
                            'file_path': project_file.file_path,
                            'created_at': project_file.created_at.isoformat() if project_file.created_at else None,
                            'total_words': analysis_data.get_total_words(),
                            'total_segments': analysis_data.get_total_segments(),
                            'language_pair': analysis_data.get_language_pair_code(),
                            'cat_tool': analysis_data.cat_tool
                        }
                    else:
                        file_info = {
                            'id': project_file.id,
                            'filename': project_file.filename,
                            'file_path': project_file.file_path,
                            'created_at': project_file.created_at.isoformat() if project_file.created_at else None,
                            'total_words': 0,
                            'total_segments': 0,
                            'language_pair': '',
                            'cat_tool': 'Unknown'
                        }
                    
                    file_list.append(file_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing file {project_file.id} data: {e}")
                    continue
            
            return file_list
            
        except Exception as e:
            self.logger.error(f"Error getting project files: {e}")
            return []
    
    def process_uploaded_file(self, uploaded_file_path: Path, 
                                target_project_id: Optional[int] = None) -> Dict[str, Any]:
            """Process an uploaded file for analysis or project addition.
            
            Args:
                uploaded_file_path: Path to uploaded file
                target_project_id: Optional project ID to add file to
                
            Returns:
                Dict[str, Any]: Processing results
            """
            result = {
                'success': False,
                'analysis_data': None,
                'errors': [],
                'warnings': [],
                'file_info': {}
            }
            
            try:
                # Validate file
                file_validation = validate_file(uploaded_file_path)
                result['errors'].extend(file_validation.errors)
                result['warnings'].extend(file_validation.warnings)
                
                if not file_validation.is_valid:
                    return result
                
                # Get file info
                result['file_info'] = FileUtils.get_file_info_detailed(uploaded_file_path)
                
                # Check if parser can handle file
                if not self.parser_factory.can_parse_file(uploaded_file_path):
                    result['errors'].append("No parser available for this file type")
                    return result
                
                # Parse file using our parse_file method
                analysis_data = self.parse_file(uploaded_file_path)
                if not analysis_data:
                    result['errors'].append("Failed to parse file")
                    return result
                
                # Convert analysis data to dict SAFELY
                try:
                    result['analysis_data'] = analysis_data.to_dict()
                except Exception as e:
                    self.logger.error(f"Error converting analysis data to dict: {e}")
                    # Create manual dict as fallback
                    result['analysis_data'] = {
                        'filename': analysis_data.filename,
                        'source_language': analysis_data.source_language,
                        'target_language': analysis_data.target_language,
                        'total_words': analysis_data.get_total_words(),
                        'total_segments': analysis_data.get_total_segments(),
                        'cat_tool': analysis_data.cat_tool,
                        'language_pair': analysis_data.get_language_pair_code(),
                        'file_path': analysis_data.file_path,
                        'analysis_date': analysis_data.analysis_date
                    }
                
                # If target project specified, add to project
                if target_project_id:
                    file_data, add_validation = self.add_file_to_project(
                        target_project_id, uploaded_file_path
                    )
                    
                    result['errors'].extend(add_validation.errors)
                    result['warnings'].extend(add_validation.warnings)
                    
                    if add_validation.is_valid:
                        result['added_to_project'] = target_project_id
                    else:
                        result['errors'].append("Failed to add file to project")
                        return result
                
                result['success'] = True
                self.logger.info(f"Successfully processed file: {uploaded_file_path.name}")
                return result
                
            except Exception as e:
                self.logger.error(f"Error processing uploaded file: {e}")
                result['errors'].append(f"Processing error: {e}")
                return result
    
    def validate_project_name_unique(self, name: str, 
                                   exclude_project_id: Optional[int] = None) -> bool:
        """Check if project name is unique.
        
        Args:
            name: Project name to check
            exclude_project_id: Project ID to exclude from check (for updates)
            
        Returns:
            bool: True if name is unique
        """
        try:
            # Search for projects with this name
            projects = self.project_repository.search_projects(name)
            
            # Filter exact matches
            exact_matches = [p for p in projects if p.name.lower() == name.lower().strip()]
            
            if exclude_project_id:
                exact_matches = [p for p in exact_matches if p.id != exclude_project_id]
            
            return len(exact_matches) == 0
            
        except Exception as e:
            self.logger.error(f"Error checking project name uniqueness: {e}")
            return False
    
    def get_supported_file_types(self) -> Dict[str, Any]:
        """Get information about supported file types.
        
        Returns:
            Dict[str, Any]: Supported file type information
        """
        try:
            return {
                'extensions': self.parser_factory.get_supported_extensions(),
                'parsers': self.parser_factory.get_parser_info(),
                'max_file_size_mb': 50  # From settings
            }
            
        except Exception as e:
            self.logger.error(f"Error getting supported file types: {e}")
            return {
                'extensions': ['.csv'],
                'parsers': {},
                'max_file_size_mb': 50
            }
    
    def _validate_project_creation(self, name: str, translator_id: int,
                                 source_language: str, target_language: str,
                                 client_id: Optional[int], mt_percentage: int) -> ValidationResult:
        """Validate project creation inputs.
        
        Args:
            name: Project name
            translator_id: Translator ID
            source_language: Source language code
            target_language: Target language code
            client_id: Optional client ID
            mt_percentage: MT percentage
            
        Returns:
            ValidationResult: Validation result
        """
        validation = ValidationResult()
        
        # Validate name
        name_validation = validate_input('project_name', name)
        validation = validation.merge(name_validation)
        
        # Check name uniqueness
        if not self.validate_project_name_unique(name):
            validation.add_error("Project name already exists")
        
        # Validate translator exists
        translator = self.translator_repository.find_by_id(translator_id)
        if not translator:
            validation.add_error("Translator not found")
        elif not translator.is_active:
            validation.add_warning("Translator is not active")
        
        # Validate client if specified
        if client_id:
            client = self.client_repository.find_by_id(client_id)
            if not client:
                validation.add_error("Client not found")
            elif not client.is_active:
                validation.add_warning("Client is not active")
        
        # Validate language codes
        source_validation = validate_input('language_code', source_language)
        target_validation = validate_input('language_code', target_language)
        validation = validation.merge(source_validation).merge(target_validation)
        
        # Check languages are different
        if source_language.strip().lower() == target_language.strip().lower():
            validation.add_error("Source and target languages must be different")
        
        # Validate MT percentage
        mt_validation = validate_input('mt_percentage', mt_percentage)
        validation = validation.merge(mt_validation)
        
        return validation
    
    def _load_project_analysis_data(self, project_id: int) -> Optional[ProjectAnalysisData]:
        """Load analysis data for all files in a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Optional[ProjectAnalysisData]: Project analysis data or None
        """
        try:
            # Get project info
            project = self.project_repository.find_by_id(project_id)
            if not project:
                return None
            
            # Get all project files
            project_files = self.project_file_repository.find_by_project_id(project_id)
            
            if not project_files:
                # Return empty analysis data
                return ProjectAnalysisData(project_name=project.name)
            
            # Create project analysis data
            project_analysis = ProjectAnalysisData(project_name=project.name)
            
            # Load analysis data for each file
            for project_file in project_files:
                try:
                    file_analysis = self.project_file_repository.get_analysis_data(project_file.id)
                    if file_analysis:
                        project_analysis.add_file_analysis(file_analysis)
                except Exception as e:
                    self.logger.warning(f"Error loading analysis for file {project_file.id}: {e}")
                    continue
            
            return project_analysis
            
        except Exception as e:
            self.logger.error(f"Error loading project analysis data: {e}")
            return None
        
    def parse_file(self, file_path: Path) -> Optional[FileAnalysisData]:
            """Parse a file and return analysis data.
            
            Args:
                file_path: Path to file to parse
                
            Returns:
                Optional[FileAnalysisData]: Parsed analysis data or None if failed
            """
            try:
                # Validate file
                file_validation = validate_file(file_path)
                if not file_validation.is_valid:
                    self.logger.error(f"File validation failed: {file_validation.errors}")
                    return None
                
                # Check if parser can handle file
                if not self.parser_factory.can_parse_file(file_path):
                    self.logger.error("No parser available for this file type")
                    return None
                
                # Parse file
                analysis_data = self.parser_factory.parse_file(file_path)
                
                if analysis_data:
                    self.logger.info(f"Successfully parsed file: {file_path.name}")
                    return analysis_data
                else:
                    self.logger.error("Failed to parse file - no data returned")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Error parsing file {file_path}: {e}")
                return None