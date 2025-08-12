import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NaturalLanguageToSQLService:
    """Service for translating natural language queries to SQL"""
    
    def __init__(self):
        self.table_mappings = {
            'survey': 'surveys',
            'response': 'survey_responses',
            'user': 'users',
            'field': 'survey_fields',
            'answer': 'field_responses'
        }
        
        self.column_mappings = {
            'surveys': {
                'title': 'title',
                'name': 'title',
                'description': 'description',
                'status': 'status',
                'created': 'created_at',
                'updated': 'updated_at',
                'published': 'published_at',
                'creator': 'creator_id'
            },
            'survey_responses': {
                'response': 'data',
                'completed': 'completed_at',
                'started': 'started_at',
                'time': 'completion_time',
                'quality': 'quality_score',
                'complete': 'is_complete'
            },
            'users': {
                'username': 'username',
                'email': 'email',
                'name': 'full_name',
                'role': 'role',
                'active': 'is_active',
                'verified': 'is_verified'
            }
        }
        
        self.aggregation_functions = {
            'count': 'COUNT',
            'average': 'AVG',
            'avg': 'AVG',
            'sum': 'SUM',
            'total': 'SUM',
            'maximum': 'MAX',
            'max': 'MAX',
            'minimum': 'MIN',
            'min': 'MIN'
        }
        
        self.time_filters = {
            'today': "DATE(created_at) = CURRENT_DATE",
            'yesterday': "DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'",
            'this week': "created_at >= DATE_TRUNC('week', CURRENT_DATE)",
            'last week': "created_at >= DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '1 week' AND created_at < DATE_TRUNC('week', CURRENT_DATE)",
            'this month': "created_at >= DATE_TRUNC('month', CURRENT_DATE)",
            'last month': "created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AND created_at < DATE_TRUNC('month', CURRENT_DATE)",
            'this year': "created_at >= DATE_TRUNC('year', CURRENT_DATE)",
            'last year': "created_at >= DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year' AND created_at < DATE_TRUNC('year', CURRENT_DATE)"
        }
    
    def translate_query(self, natural_query: str) -> Tuple[str, float, Dict]:
        """
        Translate natural language query to SQL
        Returns: (sql_query, confidence_score, metadata)
        """
        try:
            query_lower = natural_query.lower().strip()
            
            # Parse the query components
            parsed = self._parse_query_components(query_lower)
            
            # Generate SQL based on parsed components
            sql_query = self._generate_sql(parsed)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(parsed, natural_query)
            
            # Generate metadata
            metadata = {
                'parsed_components': parsed,
                'tables_used': parsed.get('tables', []),
                'aggregations': parsed.get('aggregations', []),
                'filters': parsed.get('filters', []),
                'query_type': parsed.get('query_type', 'unknown')
            }
            
            return sql_query, confidence, metadata
            
        except Exception as e:
            logger.error(f"Error translating query: {e}")
            return "", 0.0, {"error": str(e)}
    
    def _parse_query_components(self, query: str) -> Dict:
        """Parse natural language query into components"""
        components = {
            'query_type': 'select',
            'tables': [],
            'columns': [],
            'aggregations': [],
            'filters': [],
            'group_by': [],
            'order_by': [],
            'limit': None
        }
        
        # Detect query type
        if any(word in query for word in ['how many', 'count', 'number of']):
            components['query_type'] = 'count'
            components['aggregations'].append('COUNT')
        elif any(word in query for word in ['average', 'avg', 'mean']):
            components['query_type'] = 'aggregate'
            components['aggregations'].append('AVG')
        elif any(word in query for word in ['sum', 'total']):
            components['query_type'] = 'aggregate'
            components['aggregations'].append('SUM')
        elif any(word in query for word in ['max', 'maximum', 'highest']):
            components['query_type'] = 'aggregate'
            components['aggregations'].append('MAX')
        elif any(word in query for word in ['min', 'minimum', 'lowest']):
            components['query_type'] = 'aggregate'
            components['aggregations'].append('MIN')
        
        # Detect tables
        for table_alias, table_name in self.table_mappings.items():
            if table_alias in query or table_name in query:
                components['tables'].append(table_name)
        
        # If no specific table mentioned, infer from context
        if not components['tables']:
            if any(word in query for word in ['survey', 'form', 'questionnaire']):
                components['tables'].append('surveys')
            elif any(word in query for word in ['response', 'answer', 'submission']):
                components['tables'].append('survey_responses')
            elif any(word in query for word in ['user', 'person', 'respondent']):
                components['tables'].append('users')
        
        # Detect time filters
        for time_phrase, sql_condition in self.time_filters.items():
            if time_phrase in query:
                components['filters'].append(sql_condition)
        
        # Detect grouping
        if any(word in query for word in ['by', 'per', 'each', 'group']):
            # Try to identify grouping column
            if 'status' in query:
                components['group_by'].append('status')
            elif 'role' in query:
                components['group_by'].append('role')
            elif 'date' in query or 'day' in query:
                components['group_by'].append('DATE(created_at)')
            elif 'month' in query:
                components['group_by'].append('DATE_TRUNC(\'month\', created_at)')
        
        # Detect ordering
        if any(word in query for word in ['top', 'highest', 'most']):
            components['order_by'].append('DESC')
        elif any(word in query for word in ['bottom', 'lowest', 'least']):
            components['order_by'].append('ASC')
        
        # Detect limits
        numbers = re.findall(r'\b(\d+)\b', query)
        if numbers and any(word in query for word in ['top', 'first', 'limit']):
            components['limit'] = int(numbers[0])
        
        return components
    
    def _generate_sql(self, components: Dict) -> str:
        """Generate SQL query from parsed components"""
        
        # Default to surveys table if none specified
        if not components['tables']:
            components['tables'] = ['surveys']
        
        main_table = components['tables'][0]
        
        # Build SELECT clause
        if components['query_type'] == 'count':
            select_clause = "SELECT COUNT(*) as count"
        elif components['aggregations']:
            agg_func = components['aggregations'][0]
            if agg_func in ['AVG', 'SUM', 'MAX', 'MIN']:
                # Try to find appropriate numeric column
                numeric_col = self._get_numeric_column(main_table)
                select_clause = f"SELECT {agg_func}({numeric_col}) as result"
            else:
                select_clause = f"SELECT {agg_func}(*) as result"
        else:
            select_clause = "SELECT *"
        
        # Add grouping columns to SELECT if needed
        if components['group_by']:
            group_cols = ', '.join(components['group_by'])
            if components['query_type'] == 'count':
                select_clause = f"SELECT {group_cols}, COUNT(*) as count"
            elif components['aggregations']:
                agg_func = components['aggregations'][0]
                numeric_col = self._get_numeric_column(main_table)
                select_clause = f"SELECT {group_cols}, {agg_func}({numeric_col}) as result"
            else:
                select_clause = f"SELECT {group_cols}, *"
        
        # Build FROM clause
        from_clause = f"FROM {main_table}"
        
        # Build WHERE clause
        where_conditions = []
        if components['filters']:
            where_conditions.extend(components['filters'])
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build GROUP BY clause
        group_by_clause = ""
        if components['group_by']:
            group_by_clause = "GROUP BY " + ", ".join(components['group_by'])
        
        # Build ORDER BY clause
        order_by_clause = ""
        if components['order_by']:
            if components['aggregations'] or components['query_type'] == 'count':
                order_by_clause = f"ORDER BY result {components['order_by'][0]}"
            else:
                order_by_clause = f"ORDER BY created_at {components['order_by'][0]}"
        
        # Build LIMIT clause
        limit_clause = ""
        if components['limit']:
            limit_clause = f"LIMIT {components['limit']}"
        
        # Combine all clauses
        sql_parts = [select_clause, from_clause]
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)
        if limit_clause:
            sql_parts.append(limit_clause)
        
        return " ".join(sql_parts)
    
    def _get_numeric_column(self, table: str) -> str:
        """Get appropriate numeric column for aggregation"""
        numeric_columns = {
            'surveys': 'id',
            'survey_responses': 'completion_time',
            'users': 'id'
        }
        return numeric_columns.get(table, 'id')
    
    def _calculate_confidence(self, components: Dict, original_query: str) -> float:
        """Calculate confidence score for the translation"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for recognized patterns
        if components['tables']:
            confidence += 0.2
        
        if components['aggregations']:
            confidence += 0.2
        
        if components['filters']:
            confidence += 0.1
        
        # Decrease confidence for complex queries
        if len(original_query.split()) > 15:
            confidence -= 0.1
        
        # Increase confidence for common patterns
        common_patterns = [
            'how many', 'count', 'average', 'total', 'sum',
            'last week', 'this month', 'today', 'yesterday'
        ]
        
        for pattern in common_patterns:
            if pattern in original_query.lower():
                confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, str]:
        """Validate generated SQL query for safety"""
        
        # Check for dangerous operations
        dangerous_keywords = [
            'drop', 'delete', 'update', 'insert', 'alter',
            'create', 'truncate', 'grant', 'revoke'
        ]
        
        sql_lower = sql_query.lower()
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False, f"Dangerous operation detected: {keyword}"
        
        # Check for basic SQL structure
        if not sql_lower.startswith('select'):
            return False, "Query must start with SELECT"
        
        if 'from' not in sql_lower:
            return False, "Query must contain FROM clause"
        
        # Check for SQL injection patterns
        injection_patterns = [
            r"';", r"--", r"/\*", r"\*/", r"union\s+select",
            r"exec\s*\(", r"sp_", r"xp_"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_lower):
                return False, f"Potential SQL injection detected: {pattern}"
        
        return True, "Query is valid"
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get query suggestions based on partial input"""
        suggestions = []
        
        partial_lower = partial_query.lower()
        
        # Common query starters
        if not partial_query or len(partial_query) < 3:
            suggestions = [
                "How many surveys were created this month?",
                "What is the average completion time for responses?",
                "Show me the top 5 most active users",
                "Count responses by survey status",
                "What surveys were published last week?"
            ]
        else:
            # Context-aware suggestions
            if 'how many' in partial_lower:
                suggestions.extend([
                    "How many surveys were created today?",
                    "How many responses were submitted this week?",
                    "How many users are active?"
                ])
            
            if 'average' in partial_lower or 'avg' in partial_lower:
                suggestions.extend([
                    "Average completion time for surveys",
                    "Average response quality score",
                    "Average responses per survey"
                ])
            
            if 'top' in partial_lower:
                suggestions.extend([
                    "Top 10 surveys by response count",
                    "Top users by survey creation",
                    "Top performing surveys this month"
                ])
        
        return suggestions[:5]  # Return top 5 suggestions

