from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.survey import Survey, SurveyField
from app.models.response import SurveyResponse, FieldResponse

class SurveyValidationService:
    """Service for validating survey data and responses"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_survey_structure(self, survey_data: Dict) -> Tuple[bool, List[str]]:
        """Validate survey structure and configuration"""
        errors = []
        
        # Check required fields
        if not survey_data.get('title'):
            errors.append("Survey title is required")
        
        if not survey_data.get('fields'):
            errors.append("Survey must have at least one field")
        
        # Validate fields
        fields = survey_data.get('fields', {})
        if isinstance(fields, dict):
            for field_id, field_config in fields.items():
                field_errors = self._validate_field_config(field_config)
                errors.extend([f"Field '{field_id}': {error}" for error in field_errors])
        
        # Validate settings
        settings = survey_data.get('settings', {})
        if settings:
            settings_errors = self._validate_survey_settings(settings)
            errors.extend(settings_errors)
        
        return len(errors) == 0, errors
    
    def _validate_field_config(self, field_config: Dict) -> List[str]:
        """Validate individual field configuration"""
        errors = []
        
        # Check required field properties
        if not field_config.get('type'):
            errors.append("Field type is required")
        
        if not field_config.get('label'):
            errors.append("Field label is required")
        
        field_type = field_config.get('type')
        
        # Validate field type specific requirements
        if field_type in ['select', 'radio', 'checkbox']:
            options = field_config.get('options', [])
            if not options or len(options) == 0:
                errors.append(f"Field type '{field_type}' requires options")
        
        # Validate validation rules
        validation_rules = field_config.get('validation', {})
        if validation_rules:
            validation_errors = self._validate_field_validation_rules(validation_rules, field_type)
            errors.extend(validation_errors)
        
        return errors
    
    def _validate_field_validation_rules(self, rules: Dict, field_type: str) -> List[str]:
        """Validate field validation rules"""
        errors = []
        
        # Check if validation rules are appropriate for field type
        if field_type == 'email' and 'pattern' in rules:
            pattern = rules['pattern']
            try:
                re.compile(pattern)
            except re.error:
                errors.append("Invalid regex pattern for email validation")
        
        if field_type in ['number', 'integer']:
            if 'min' in rules and 'max' in rules:
                if rules['min'] > rules['max']:
                    errors.append("Minimum value cannot be greater than maximum value")
        
        if field_type == 'text':
            if 'minLength' in rules and 'maxLength' in rules:
                if rules['minLength'] > rules['maxLength']:
                    errors.append("Minimum length cannot be greater than maximum length")
        
        return errors
    
    def _validate_survey_settings(self, settings: Dict) -> List[str]:
        """Validate survey settings"""
        errors = []
        
        # Validate response limits
        max_responses = settings.get('maxResponses')
        if max_responses is not None and max_responses <= 0:
            errors.append("Maximum responses must be a positive number")
        
        # Validate time limits
        time_limit = settings.get('timeLimit')
        if time_limit is not None and time_limit <= 0:
            errors.append("Time limit must be a positive number")
        
        # Validate expiration date
        expires_at = settings.get('expiresAt')
        if expires_at:
            try:
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if expiry_date <= datetime.utcnow():
                    errors.append("Expiration date must be in the future")
            except ValueError:
                errors.append("Invalid expiration date format")
        
        return errors
    
    def validate_response_data(self, survey_id: int, response_data: Dict) -> Tuple[bool, List[str]]:
        """Validate survey response data"""
        errors = []
        
        # Get survey configuration
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            errors.append("Survey not found")
            return False, errors
        
        if not survey.fields:
            errors.append("Survey has no fields configured")
            return False, errors
        
        # Validate each field response
        for field_id, field_config in survey.fields.items():
            response_value = response_data.get(field_id)
            
            # Check required fields
            if field_config.get('required', False) and (response_value is None or response_value == ''):
                errors.append(f"Field '{field_config.get('label', field_id)}' is required")
                continue
            
            # Skip validation if field is not required and empty
            if response_value is None or response_value == '':
                continue
            
            # Validate field value
            field_errors = self._validate_field_response(field_config, response_value)
            errors.extend([f"Field '{field_config.get('label', field_id)}': {error}" for error in field_errors])
        
        return len(errors) == 0, errors
    
    def _validate_field_response(self, field_config: Dict, value: Any) -> List[str]:
        """Validate individual field response value"""
        errors = []
        field_type = field_config.get('type')
        validation_rules = field_config.get('validation', {})
        
        # Type-specific validation
        if field_type == 'email':
            if not self._is_valid_email(str(value)):
                errors.append("Invalid email format")
        
        elif field_type == 'number':
            try:
                num_value = float(value)
                if 'min' in validation_rules and num_value < validation_rules['min']:
                    errors.append(f"Value must be at least {validation_rules['min']}")
                if 'max' in validation_rules and num_value > validation_rules['max']:
                    errors.append(f"Value must be at most {validation_rules['max']}")
            except (ValueError, TypeError):
                errors.append("Invalid number format")
        
        elif field_type == 'integer':
            try:
                int_value = int(value)
                if 'min' in validation_rules and int_value < validation_rules['min']:
                    errors.append(f"Value must be at least {validation_rules['min']}")
                if 'max' in validation_rules and int_value > validation_rules['max']:
                    errors.append(f"Value must be at most {validation_rules['max']}")
            except (ValueError, TypeError):
                errors.append("Invalid integer format")
        
        elif field_type == 'text':
            text_value = str(value)
            if 'minLength' in validation_rules and len(text_value) < validation_rules['minLength']:
                errors.append(f"Text must be at least {validation_rules['minLength']} characters")
            if 'maxLength' in validation_rules and len(text_value) > validation_rules['maxLength']:
                errors.append(f"Text must be at most {validation_rules['maxLength']} characters")
            if 'pattern' in validation_rules:
                try:
                    if not re.match(validation_rules['pattern'], text_value):
                        errors.append("Text does not match required pattern")
                except re.error:
                    errors.append("Invalid validation pattern")
        
        elif field_type in ['select', 'radio']:
            options = field_config.get('options', [])
            valid_values = [opt.get('value') if isinstance(opt, dict) else opt for opt in options]
            if value not in valid_values:
                errors.append("Invalid option selected")
        
        elif field_type == 'checkbox':
            if not isinstance(value, list):
                errors.append("Checkbox field must be a list of values")
            else:
                options = field_config.get('options', [])
                valid_values = [opt.get('value') if isinstance(opt, dict) else opt for opt in options]
                for selected_value in value:
                    if selected_value not in valid_values:
                        errors.append(f"Invalid checkbox option: {selected_value}")
        
        elif field_type == 'date':
            try:
                datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid date format")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def calculate_response_quality_score(self, survey_id: int, response_data: Dict) -> float:
        """Calculate quality score for a response"""
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey or not survey.fields:
            return 0.0
        
        total_fields = len(survey.fields)
        completed_fields = 0
        quality_points = 0.0
        
        for field_id, field_config in survey.fields.items():
            response_value = response_data.get(field_id)
            
            if response_value is not None and response_value != '':
                completed_fields += 1
                
                # Award points based on response quality
                field_type = field_config.get('type')
                
                if field_type == 'text':
                    text_length = len(str(response_value))
                    if text_length > 50:
                        quality_points += 1.0
                    elif text_length > 20:
                        quality_points += 0.7
                    else:
                        quality_points += 0.5
                
                elif field_type in ['select', 'radio', 'checkbox']:
                    quality_points += 1.0
                
                elif field_type in ['number', 'integer']:
                    quality_points += 0.8
                
                elif field_type == 'email':
                    if self._is_valid_email(str(response_value)):
                        quality_points += 1.0
                    else:
                        quality_points += 0.3
                
                else:
                    quality_points += 0.6
        
        # Calculate completion ratio
        completion_ratio = completed_fields / total_fields if total_fields > 0 else 0
        
        # Calculate average quality per field
        avg_quality = quality_points / total_fields if total_fields > 0 else 0
        
        # Final score is weighted average of completion and quality
        final_score = (completion_ratio * 0.4) + (avg_quality * 0.6)
        
        return min(1.0, max(0.0, final_score))

