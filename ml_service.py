import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class AdaptiveSurveyService:
    """Service for adaptive survey questioning using ML models"""
    
    def __init__(self):
        self.question_patterns = {
            'satisfaction': {
                'follow_up_low': [
                    "What specific aspects could be improved?",
                    "Can you tell us more about your concerns?",
                    "What would make your experience better?"
                ],
                'follow_up_high': [
                    "What did you like most about your experience?",
                    "Would you recommend us to others?",
                    "Any additional positive feedback?"
                ]
            },
            'usage': {
                'follow_up_frequent': [
                    "What features do you use most often?",
                    "How has this impacted your workflow?",
                    "Any advanced features you'd like to see?"
                ],
                'follow_up_infrequent': [
                    "What prevents you from using this more often?",
                    "What would encourage more frequent use?",
                    "Are there any barriers we should address?"
                ]
            }
        }
        
        self.response_patterns = defaultdict(list)
        self.user_profiles = defaultdict(dict)
    
    def get_next_question(self, survey_id: int, user_id: int, current_responses: Dict) -> Optional[Dict]:
        """
        Get the next adaptive question based on current responses
        Returns: question configuration or None if survey is complete
        """
        try:
            # Analyze current responses to determine next question
            response_analysis = self._analyze_responses(current_responses)
            
            # Get user profile for personalization
            user_profile = self._get_user_profile(user_id)
            
            # Determine next question based on analysis
            next_question = self._select_next_question(
                survey_id, response_analysis, user_profile, current_responses
            )
            
            return next_question
            
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return None
    
    def _analyze_responses(self, responses: Dict) -> Dict:
        """Analyze current responses to understand patterns"""
        analysis = {
            'sentiment_score': 0.0,
            'completion_level': 0.0,
            'response_quality': 0.0,
            'key_themes': [],
            'satisfaction_indicators': [],
            'engagement_level': 'medium'
        }
        
        if not responses:
            return analysis
        
        # Calculate completion level
        total_fields = len(responses)
        completed_fields = sum(1 for v in responses.values() if v is not None and v != '')
        analysis['completion_level'] = completed_fields / total_fields if total_fields > 0 else 0
        
        # Analyze sentiment from text responses
        text_responses = [str(v) for v in responses.values() if isinstance(v, str) and len(str(v)) > 10]
        if text_responses:
            analysis['sentiment_score'] = self._calculate_sentiment_score(text_responses)
        
        # Analyze satisfaction indicators
        satisfaction_fields = ['satisfaction', 'rating', 'score', 'experience']
        for field, value in responses.items():
            if any(indicator in field.lower() for indicator in satisfaction_fields):
                if isinstance(value, (int, float)):
                    analysis['satisfaction_indicators'].append(value)
        
        # Calculate response quality
        analysis['response_quality'] = self._calculate_response_quality(responses)
        
        # Determine engagement level
        analysis['engagement_level'] = self._determine_engagement_level(responses)
        
        return analysis
    
    def _calculate_sentiment_score(self, text_responses: List[str]) -> float:
        """Calculate sentiment score from text responses (simplified)"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'satisfied', 'happy', 'pleased'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike',
            'disappointed', 'frustrated', 'angry', 'unsatisfied', 'poor'
        ]
        
        total_score = 0
        total_words = 0
        
        for text in text_responses:
            words = text.lower().split()
            total_words += len(words)
            
            for word in words:
                if word in positive_words:
                    total_score += 1
                elif word in negative_words:
                    total_score -= 1
        
        return total_score / total_words if total_words > 0 else 0.0
    
    def _calculate_response_quality(self, responses: Dict) -> float:
        """Calculate quality score of responses"""
        quality_score = 0.0
        total_responses = len(responses)
        
        if total_responses == 0:
            return 0.0
        
        for value in responses.values():
            if value is None or value == '':
                continue
            
            if isinstance(value, str):
                # Text quality based on length and content
                if len(value.strip()) > 20:
                    quality_score += 1.0
                elif len(value.strip()) > 5:
                    quality_score += 0.7
                else:
                    quality_score += 0.3
            else:
                # Non-text responses get full score if present
                quality_score += 1.0
        
        return quality_score / total_responses
    
    def _determine_engagement_level(self, responses: Dict) -> str:
        """Determine user engagement level"""
        if not responses:
            return 'low'
        
        # Count meaningful responses
        meaningful_responses = 0
        total_responses = len(responses)
        
        for value in responses.values():
            if value is None or value == '':
                continue
            
            if isinstance(value, str) and len(value.strip()) > 10:
                meaningful_responses += 1
            elif not isinstance(value, str):
                meaningful_responses += 1
        
        engagement_ratio = meaningful_responses / total_responses if total_responses > 0 else 0
        
        if engagement_ratio > 0.8:
            return 'high'
        elif engagement_ratio > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _get_user_profile(self, user_id: int) -> Dict:
        """Get or create user profile for personalization"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'response_history': [],
                'preferred_question_types': [],
                'engagement_patterns': {},
                'satisfaction_trends': []
            }
        
        return self.user_profiles[user_id]
    
    def _select_next_question(self, survey_id: int, analysis: Dict, user_profile: Dict, current_responses: Dict) -> Optional[Dict]:
        """Select the next adaptive question"""
        
        # Check if we should ask follow-up questions based on responses
        satisfaction_scores = analysis.get('satisfaction_indicators', [])
        
        if satisfaction_scores:
            avg_satisfaction = np.mean(satisfaction_scores)
            
            if avg_satisfaction <= 2:  # Low satisfaction
                return self._create_follow_up_question('satisfaction', 'follow_up_low', analysis)
            elif avg_satisfaction >= 4:  # High satisfaction
                return self._create_follow_up_question('satisfaction', 'follow_up_high', analysis)
        
        # Check engagement level for adaptive questioning
        engagement = analysis.get('engagement_level', 'medium')
        
        if engagement == 'low':
            # Ask simpler, more engaging questions
            return self._create_engagement_question(analysis)
        elif engagement == 'high':
            # Ask more detailed, complex questions
            return self._create_detailed_question(analysis)
        
        # Default: no additional questions
        return None
    
    def _create_follow_up_question(self, category: str, follow_up_type: str, analysis: Dict) -> Dict:
        """Create a follow-up question based on category and type"""
        questions = self.question_patterns.get(category, {}).get(follow_up_type, [])
        
        if not questions:
            return None
        
        # Select question based on context
        question_text = questions[0]  # Simple selection for now
        
        return {
            'id': f'adaptive_{category}_{follow_up_type}',
            'type': 'text',
            'label': question_text,
            'required': False,
            'adaptive': True,
            'category': category,
            'context': analysis
        }
    
    def _create_engagement_question(self, analysis: Dict) -> Dict:
        """Create an engaging question for low-engagement users"""
        engaging_questions = [
            "What's the most important thing we should know?",
            "If you could change one thing, what would it be?",
            "What matters most to you in this experience?"
        ]
        
        return {
            'id': 'adaptive_engagement',
            'type': 'text',
            'label': engaging_questions[0],
            'required': False,
            'adaptive': True,
            'category': 'engagement'
        }
    
    def _create_detailed_question(self, analysis: Dict) -> Dict:
        """Create a detailed question for high-engagement users"""
        detailed_questions = [
            "Can you provide more specific details about your experience?",
            "What additional features or improvements would you suggest?",
            "How do you think this could be enhanced further?"
        ]
        
        return {
            'id': 'adaptive_detailed',
            'type': 'textarea',
            'label': detailed_questions[0],
            'required': False,
            'adaptive': True,
            'category': 'detailed'
        }
    
    def update_user_profile(self, user_id: int, response_data: Dict, completion_time: float):
        """Update user profile based on response"""
        profile = self._get_user_profile(user_id)
        
        # Add to response history
        profile['response_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'response_data': response_data,
            'completion_time': completion_time,
            'quality_score': self._calculate_response_quality(response_data)
        })
        
        # Update engagement patterns
        engagement = self._determine_engagement_level(response_data)
        if engagement not in profile['engagement_patterns']:
            profile['engagement_patterns'][engagement] = 0
        profile['engagement_patterns'][engagement] += 1
        
        # Update satisfaction trends
        satisfaction_fields = ['satisfaction', 'rating', 'score']
        for field, value in response_data.items():
            if any(indicator in field.lower() for indicator in satisfaction_fields):
                if isinstance(value, (int, float)):
                    profile['satisfaction_trends'].append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'score': value
                    })
        
        # Keep only recent history (last 50 responses)
        if len(profile['response_history']) > 50:
            profile['response_history'] = profile['response_history'][-50:]
        
        if len(profile['satisfaction_trends']) > 50:
            profile['satisfaction_trends'] = profile['satisfaction_trends'][-50:]


class ReportGenerationService:
    """Service for generating natural language reports from survey data"""
    
    def __init__(self):
        self.report_templates = {
            'summary': {
                'title': 'Survey Summary Report',
                'sections': ['overview', 'key_findings', 'demographics', 'recommendations']
            },
            'detailed': {
                'title': 'Detailed Analysis Report',
                'sections': ['overview', 'response_analysis', 'statistical_summary', 'trends', 'recommendations']
            },
            'executive': {
                'title': 'Executive Summary',
                'sections': ['overview', 'key_metrics', 'critical_insights', 'action_items']
            }
        }
    
    def generate_report(self, survey_data: Dict, responses: List[Dict], report_type: str = 'summary') -> Dict:
        """
        Generate a natural language report from survey data
        Returns: report dictionary with sections and content
        """
        try:
            template = self.report_templates.get(report_type, self.report_templates['summary'])
            
            # Analyze the data
            analysis = self._analyze_survey_data(survey_data, responses)
            
            # Generate report sections
            report = {
                'title': template['title'],
                'generated_at': datetime.utcnow().isoformat(),
                'survey_title': survey_data.get('title', 'Untitled Survey'),
                'total_responses': len(responses),
                'sections': {}
            }
            
            for section_name in template['sections']:
                section_content = self._generate_section(section_name, analysis, survey_data, responses)
                report['sections'][section_name] = section_content
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                'title': 'Error Report',
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _analyze_survey_data(self, survey_data: Dict, responses: List[Dict]) -> Dict:
        """Analyze survey data for report generation"""
        analysis = {
            'total_responses': len(responses),
            'completion_rate': 0.0,
            'average_completion_time': 0.0,
            'response_quality_score': 0.0,
            'field_statistics': {},
            'sentiment_analysis': {},
            'trends': {},
            'demographics': {}
        }
        
        if not responses:
            return analysis
        
        # Calculate completion rate
        completed_responses = sum(1 for r in responses if r.get('is_complete', False))
        analysis['completion_rate'] = completed_responses / len(responses) * 100
        
        # Calculate average completion time
        completion_times = [r.get('completion_time', 0) for r in responses if r.get('completion_time')]
        if completion_times:
            analysis['average_completion_time'] = np.mean(completion_times)
        
        # Analyze individual fields
        fields = survey_data.get('fields', {})
        for field_id, field_config in fields.items():
            field_stats = self._analyze_field_responses(field_id, field_config, responses)
            analysis['field_statistics'][field_id] = field_stats
        
        # Overall quality score
        quality_scores = [r.get('quality_score', 0) for r in responses if r.get('quality_score')]
        if quality_scores:
            analysis['response_quality_score'] = np.mean(quality_scores)
        
        return analysis
    
    def _analyze_field_responses(self, field_id: str, field_config: Dict, responses: List[Dict]) -> Dict:
        """Analyze responses for a specific field"""
        field_stats = {
            'field_type': field_config.get('type', 'unknown'),
            'field_label': field_config.get('label', field_id),
            'response_count': 0,
            'response_rate': 0.0,
            'values': [],
            'statistics': {}
        }
        
        # Extract values for this field
        for response in responses:
            response_data = response.get('data', {})
            if field_id in response_data:
                value = response_data[field_id]
                if value is not None and value != '':
                    field_stats['values'].append(value)
                    field_stats['response_count'] += 1
        
        field_stats['response_rate'] = field_stats['response_count'] / len(responses) * 100 if responses else 0
        
        # Calculate statistics based on field type
        if field_config.get('type') == 'number' and field_stats['values']:
            numeric_values = [float(v) for v in field_stats['values'] if isinstance(v, (int, float))]
            if numeric_values:
                field_stats['statistics'] = {
                    'mean': np.mean(numeric_values),
                    'median': np.median(numeric_values),
                    'std': np.std(numeric_values),
                    'min': np.min(numeric_values),
                    'max': np.max(numeric_values)
                }
        
        elif field_config.get('type') in ['select', 'radio', 'checkbox']:
            # Count frequencies for categorical data
            if field_config.get('type') == 'checkbox':
                # Flatten checkbox arrays
                all_values = []
                for value in field_stats['values']:
                    if isinstance(value, list):
                        all_values.extend(value)
                    else:
                        all_values.append(value)
                value_counts = Counter(all_values)
            else:
                value_counts = Counter(field_stats['values'])
            
            field_stats['statistics'] = {
                'value_counts': dict(value_counts),
                'most_common': value_counts.most_common(3)
            }
        
        elif field_config.get('type') == 'text':
            # Text analysis
            text_values = [str(v) for v in field_stats['values'] if v]
            if text_values:
                field_stats['statistics'] = {
                    'average_length': np.mean([len(text) for text in text_values]),
                    'total_words': sum(len(text.split()) for text in text_values),
                    'common_words': self._get_common_words(text_values)
                }
        
        return field_stats
    
    def _get_common_words(self, texts: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most common words from text responses"""
        # Simple word counting (in production, use proper NLP)
        all_words = []
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        for text in texts:
            words = text.lower().split()
            for word in words:
                # Simple word cleaning
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 2 and word not in stop_words:
                    all_words.append(word)
        
        return Counter(all_words).most_common(top_n)
    
    def _generate_section(self, section_name: str, analysis: Dict, survey_data: Dict, responses: List[Dict]) -> Dict:
        """Generate a specific section of the report"""
        
        if section_name == 'overview':
            return self._generate_overview_section(analysis, survey_data)
        elif section_name == 'key_findings':
            return self._generate_key_findings_section(analysis, survey_data)
        elif section_name == 'key_metrics':
            return self._generate_key_metrics_section(analysis)
        elif section_name == 'response_analysis':
            return self._generate_response_analysis_section(analysis)
        elif section_name == 'statistical_summary':
            return self._generate_statistical_summary_section(analysis)
        elif section_name == 'demographics':
            return self._generate_demographics_section(analysis)
        elif section_name == 'trends':
            return self._generate_trends_section(analysis)
        elif section_name == 'recommendations':
            return self._generate_recommendations_section(analysis)
        elif section_name == 'critical_insights':
            return self._generate_critical_insights_section(analysis)
        elif section_name == 'action_items':
            return self._generate_action_items_section(analysis)
        else:
            return {'title': section_name.title(), 'content': 'Section not implemented'}
    
    def _generate_overview_section(self, analysis: Dict, survey_data: Dict) -> Dict:
        """Generate overview section"""
        total_responses = analysis['total_responses']
        completion_rate = analysis['completion_rate']
        avg_time = analysis['average_completion_time']
        
        content = f"""
        This report analyzes {total_responses} responses collected for the survey "{survey_data.get('title', 'Untitled Survey')}".
        
        The survey achieved a completion rate of {completion_rate:.1f}%, with respondents taking an average of {avg_time:.1f} seconds to complete.
        
        The overall response quality score is {analysis['response_quality_score']:.2f} out of 1.0, indicating {'high' if analysis['response_quality_score'] > 0.7 else 'moderate' if analysis['response_quality_score'] > 0.4 else 'low'} quality responses.
        """
        
        return {
            'title': 'Overview',
            'content': content.strip(),
            'metrics': {
                'total_responses': total_responses,
                'completion_rate': completion_rate,
                'average_completion_time': avg_time,
                'quality_score': analysis['response_quality_score']
            }
        }
    
    def _generate_key_findings_section(self, analysis: Dict, survey_data: Dict) -> Dict:
        """Generate key findings section"""
        findings = []
        
        # Analyze field statistics for key insights
        for field_id, field_stats in analysis['field_statistics'].items():
            if field_stats['response_rate'] > 80:
                findings.append(f"High engagement on '{field_stats['field_label']}' with {field_stats['response_rate']:.1f}% response rate")
            
            if field_stats['field_type'] == 'number' and 'statistics' in field_stats:
                stats = field_stats['statistics']
                findings.append(f"'{field_stats['field_label']}' averaged {stats['mean']:.2f} (range: {stats['min']:.2f} - {stats['max']:.2f})")
            
            elif field_stats['field_type'] in ['select', 'radio'] and 'statistics' in field_stats:
                most_common = field_stats['statistics'].get('most_common', [])
                if most_common:
                    top_choice = most_common[0]
                    findings.append(f"Most common response for '{field_stats['field_label']}' was '{top_choice[0]}' ({top_choice[1]} responses)")
        
        content = "Key findings from the survey analysis:\n\n" + "\n".join(f"• {finding}" for finding in findings[:5])
        
        return {
            'title': 'Key Findings',
            'content': content,
            'findings': findings
        }
    
    def _generate_recommendations_section(self, analysis: Dict) -> Dict:
        """Generate recommendations section"""
        recommendations = []
        
        # Generate recommendations based on analysis
        if analysis['completion_rate'] < 70:
            recommendations.append("Consider shortening the survey or making it more engaging to improve completion rates")
        
        if analysis['response_quality_score'] < 0.5:
            recommendations.append("Review question clarity and consider adding examples to improve response quality")
        
        if analysis['average_completion_time'] > 300:  # 5 minutes
            recommendations.append("Survey may be too long - consider reducing the number of questions")
        
        # Field-specific recommendations
        for field_id, field_stats in analysis['field_statistics'].items():
            if field_stats['response_rate'] < 50:
                recommendations.append(f"Consider making '{field_stats['field_label']}' optional or revising the question")
        
        if not recommendations:
            recommendations.append("Survey performance is good - continue with current approach")
        
        content = "Recommendations for improving future surveys:\n\n" + "\n".join(f"• {rec}" for rec in recommendations)
        
        return {
            'title': 'Recommendations',
            'content': content,
            'recommendations': recommendations
        }
    
    def _generate_key_metrics_section(self, analysis: Dict) -> Dict:
        """Generate key metrics section for executive summary"""
        metrics = {
            'Response Rate': f"{analysis['completion_rate']:.1f}%",
            'Total Responses': analysis['total_responses'],
            'Average Completion Time': f"{analysis['average_completion_time']:.1f} seconds",
            'Data Quality Score': f"{analysis['response_quality_score']:.2f}/1.0"
        }
        
        content = "Key Performance Metrics:\n\n" + "\n".join(f"• {k}: {v}" for k, v in metrics.items())
        
        return {
            'title': 'Key Metrics',
            'content': content,
            'metrics': metrics
        }
    
    def _generate_critical_insights_section(self, analysis: Dict) -> Dict:
        """Generate critical insights for executive summary"""
        insights = []
        
        # Critical insights based on data
        if analysis['completion_rate'] > 85:
            insights.append("Excellent survey engagement with high completion rates")
        elif analysis['completion_rate'] < 50:
            insights.append("Low completion rates indicate potential survey issues")
        
        if analysis['response_quality_score'] > 0.8:
            insights.append("High-quality responses provide reliable data for decision-making")
        elif analysis['response_quality_score'] < 0.4:
            insights.append("Response quality concerns may affect data reliability")
        
        content = "Critical Insights:\n\n" + "\n".join(f"• {insight}" for insight in insights)
        
        return {
            'title': 'Critical Insights',
            'content': content,
            'insights': insights
        }
    
    def _generate_action_items_section(self, analysis: Dict) -> Dict:
        """Generate action items for executive summary"""
        actions = []
        
        # Generate actionable items
        if analysis['completion_rate'] < 70:
            actions.append("Immediate: Review and optimize survey length and question clarity")
        
        if analysis['response_quality_score'] < 0.5:
            actions.append("Short-term: Implement response validation and quality checks")
        
        actions.append("Ongoing: Monitor response patterns and adjust survey strategy accordingly")
        
        content = "Recommended Action Items:\n\n" + "\n".join(f"• {action}" for action in actions)
        
        return {
            'title': 'Action Items',
            'content': content,
            'actions': actions
        }
    
    # Placeholder methods for other sections
    def _generate_response_analysis_section(self, analysis: Dict) -> Dict:
        return {'title': 'Response Analysis', 'content': 'Detailed response analysis would go here'}
    
    def _generate_statistical_summary_section(self, analysis: Dict) -> Dict:
        return {'title': 'Statistical Summary', 'content': 'Statistical summary would go here'}
    
    def _generate_demographics_section(self, analysis: Dict) -> Dict:
        return {'title': 'Demographics', 'content': 'Demographic analysis would go here'}
    
    def _generate_trends_section(self, analysis: Dict) -> Dict:
        return {'title': 'Trends', 'content': 'Trend analysis would go here'}

