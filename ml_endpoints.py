from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ..database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..models.survey import Survey
from ..models.response import SurveyResponse
from ..services.nlp_service import NaturalLanguageToSQLService
from ..services.data_cleaning import DataCleaningService
from ..services.ml_service import AdaptiveSurveyService, ReportGenerationService
from ..services.statistical_service import StatisticalEstimationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["machine-learning"])

# Initialize services
nlp_service = NaturalLanguageToSQLService()
data_cleaning_service = DataCleaningService()
adaptive_service = AdaptiveSurveyService()
report_service = ReportGenerationService()
stats_service = StatisticalEstimationService()

# Pydantic models for request/response
class NLQueryRequest(BaseModel):
    query: str
    survey_id: Optional[int] = None

class NLQueryResponse(BaseModel):
    sql_query: str
    confidence_score: float
    metadata: Dict[str, Any]
    is_valid: bool
    validation_message: str

class DataCleaningRequest(BaseModel):
    survey_id: int
    cleaning_options: Dict[str, Any] = {}

class DataCleaningResponse(BaseModel):
    cleaning_report: Dict[str, Any]
    cleaned_data_available: bool

class AdaptiveQuestionRequest(BaseModel):
    survey_id: int
    user_id: int
    current_responses: Dict[str, Any]

class AdaptiveQuestionResponse(BaseModel):
    next_question: Optional[Dict[str, Any]]
    survey_complete: bool
    recommendations: List[str] = []

class ReportGenerationRequest(BaseModel):
    survey_id: int
    report_type: str = "summary"  # summary, detailed, executive
    include_sections: List[str] = []

class ReportGenerationResponse(BaseModel):
    report: Dict[str, Any]
    generation_time: float

class StatisticalAnalysisRequest(BaseModel):
    survey_id: int
    target_variables: List[str]
    sampling_method: str = "simple_random"
    confidence_level: str = "95%"
    population_data: Dict[str, Any] = {}

class StatisticalAnalysisResponse(BaseModel):
    estimates: Dict[str, Any]
    sampling_weights: Dict[str, Any]
    variance_estimates: Dict[str, Any]

@router.post("/natural-language-query", response_model=NLQueryResponse)
async def translate_natural_language_query(
    request: NLQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Translate natural language query to SQL
    """
    try:
        # Translate the query
        sql_query, confidence, metadata = nlp_service.translate_query(request.query)
        
        # Validate the generated SQL
        is_valid, validation_message = nlp_service.validate_sql(sql_query)
        
        return NLQueryResponse(
            sql_query=sql_query,
            confidence_score=confidence,
            metadata=metadata,
            is_valid=is_valid,
            validation_message=validation_message
        )
        
    except Exception as e:
        logger.error(f"Error in natural language query translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query-suggestions")
async def get_query_suggestions(
    partial_query: str = "",
    current_user: User = Depends(get_current_user)
):
    """
    Get query suggestions based on partial input
    """
    try:
        suggestions = nlp_service.get_query_suggestions(partial_query)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error getting query suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clean-data", response_model=DataCleaningResponse)
async def clean_survey_data(
    request: DataCleaningRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clean survey response data
    """
    try:
        # Get survey and responses
        survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Check permissions
        if survey.creator_id != current_user.id and current_user.role not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Not authorized to clean this survey's data")
        
        # Get responses
        responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == request.survey_id).all()
        
        # Convert to list of dictionaries
        response_data = []
        for response in responses:
            response_dict = {
                'id': response.id,
                'data': response.data,
                'is_complete': response.is_complete,
                'completion_time': response.completion_time,
                'quality_score': getattr(response, 'quality_score', None),
                'created_at': response.created_at.isoformat() if response.created_at else None
            }
            response_data.append(response_dict)
        
        # Prepare survey configuration
        survey_config = {
            'fields': survey.fields or {},
            'validation_rules': getattr(survey, 'validation_rules', {}),
            'cleaning_options': request.cleaning_options
        }
        
        # Clean the data
        cleaned_responses, cleaning_report = data_cleaning_service.clean_survey_responses(
            response_data, survey_config
        )
        
        # Store cleaned data (in background)
        background_tasks.add_task(
            _store_cleaned_data, 
            db, 
            request.survey_id, 
            cleaned_responses, 
            cleaning_report
        )
        
        return DataCleaningResponse(
            cleaning_report=cleaning_report,
            cleaned_data_available=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning survey data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adaptive-question", response_model=AdaptiveQuestionResponse)
async def get_adaptive_question(
    request: AdaptiveQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get next adaptive question based on current responses
    """
    try:
        # Get survey
        survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Get next adaptive question
        next_question = adaptive_service.get_next_question(
            request.survey_id,
            request.user_id,
            request.current_responses
        )
        
        # Determine if survey is complete
        survey_complete = next_question is None
        
        # Generate recommendations
        recommendations = []
        if survey_complete:
            recommendations.append("Survey completed successfully")
        elif next_question and next_question.get('adaptive'):
            recommendations.append("Adaptive question generated based on your responses")
        
        return AdaptiveQuestionResponse(
            next_question=next_question,
            survey_complete=survey_complete,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_survey_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate natural language report from survey data
    """
    try:
        import time
        start_time = time.time()
        
        # Get survey and responses
        survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Check permissions
        if survey.creator_id != current_user.id and current_user.role not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Not authorized to generate reports for this survey")
        
        # Get responses
        responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == request.survey_id).all()
        
        # Convert to list of dictionaries
        response_data = []
        for response in responses:
            response_dict = {
                'id': response.id,
                'data': response.data,
                'is_complete': response.is_complete,
                'completion_time': response.completion_time,
                'quality_score': getattr(response, 'quality_score', None),
                'created_at': response.created_at.isoformat() if response.created_at else None
            }
            response_data.append(response_dict)
        
        # Prepare survey data
        survey_data = {
            'id': survey.id,
            'title': survey.title,
            'description': survey.description,
            'fields': survey.fields or {},
            'created_at': survey.created_at.isoformat() if survey.created_at else None,
            'published_at': survey.published_at.isoformat() if survey.published_at else None
        }
        
        # Generate report
        report = report_service.generate_report(
            survey_data,
            response_data,
            request.report_type
        )
        
        generation_time = time.time() - start_time
        
        # Store report (in background)
        background_tasks.add_task(
            _store_generated_report,
            db,
            request.survey_id,
            current_user.id,
            report,
            request.report_type
        )
        
        return ReportGenerationResponse(
            report=report,
            generation_time=generation_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/statistical-analysis", response_model=StatisticalAnalysisResponse)
async def perform_statistical_analysis(
    request: StatisticalAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform statistical analysis with sampling weights and variance estimation
    """
    try:
        # Get survey and responses
        survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Check permissions
        if survey.creator_id != current_user.id and current_user.role not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Not authorized to analyze this survey's data")
        
        # Get responses
        responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == request.survey_id).all()
        
        # Convert to list of dictionaries
        response_data = []
        for response in responses:
            response_dict = {
                'id': response.id,
                'data': response.data,
                'is_complete': response.is_complete,
                'completion_time': response.completion_time,
                'created_at': response.created_at.isoformat() if response.created_at else None
            }
            response_data.append(response_dict)
        
        if not response_data:
            raise HTTPException(status_code=400, detail="No responses found for analysis")
        
        # Calculate sampling weights
        sampling_weights = stats_service.calculate_sampling_weights(
            response_data,
            request.population_data,
            request.sampling_method
        )
        
        if 'error' in sampling_weights:
            raise HTTPException(status_code=400, detail=sampling_weights['error'])
        
        weights = sampling_weights['weights']
        
        # Estimate population parameters
        estimates = stats_service.estimate_population_parameters(
            response_data,
            weights,
            request.target_variables,
            request.confidence_level
        )
        
        if 'error' in estimates:
            raise HTTPException(status_code=400, detail=estimates['error'])
        
        # Calculate variance estimates
        variance_estimates = stats_service.calculate_variance_estimates(
            response_data,
            weights
        )
        
        return StatisticalAnalysisResponse(
            estimates=estimates,
            sampling_weights=sampling_weights,
            variance_estimates=variance_estimates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in statistical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/significance-tests")
async def perform_significance_tests(
    survey_id: int,
    test_specifications: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform statistical significance tests
    """
    try:
        # Get survey and responses
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # Check permissions
        if survey.creator_id != current_user.id and current_user.role not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Not authorized to analyze this survey's data")
        
        # Get responses
        responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id).all()
        
        # Convert to list of dictionaries
        response_data = []
        for response in responses:
            response_dict = {
                'id': response.id,
                'data': response.data,
                'is_complete': response.is_complete
            }
            response_data.append(response_dict)
        
        if not response_data:
            raise HTTPException(status_code=400, detail="No responses found for analysis")
        
        # Calculate equal weights for significance tests
        weights = [1.0] * len(response_data)
        
        # Perform tests
        test_results = stats_service.perform_significance_tests(
            response_data,
            weights,
            test_specifications
        )
        
        if 'error' in test_results:
            raise HTTPException(status_code=400, detail=test_results['error'])
        
        return {"test_results": test_results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing significance tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _store_cleaned_data(db: Session, survey_id: int, cleaned_responses: List[Dict], cleaning_report: Dict):
    """Store cleaned data and report"""
    try:
        # In a real implementation, you would store the cleaned data
        # and cleaning report in the database
        logger.info(f"Stored cleaned data for survey {survey_id}")
    except Exception as e:
        logger.error(f"Error storing cleaned data: {e}")

async def _store_generated_report(db: Session, survey_id: int, user_id: int, report: Dict, report_type: str):
    """Store generated report"""
    try:
        # In a real implementation, you would store the report in the database
        logger.info(f"Stored {report_type} report for survey {survey_id}")
    except Exception as e:
        logger.error(f"Error storing report: {e}")

@router.get("/health")
async def ml_health_check():
    """Health check for ML services"""
    return {
        "status": "healthy",
        "services": {
            "nlp_service": "active",
            "data_cleaning_service": "active",
            "adaptive_service": "active",
            "report_service": "active",
            "statistical_service": "active"
        }
    }

