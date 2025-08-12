import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import logging
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

class StatisticalEstimationService:
    """Service for statistical estimation and analysis of survey data"""
    
    def __init__(self):
        self.confidence_levels = {
            '90%': 1.645,
            '95%': 1.96,
            '99%': 2.576
        }
        
        self.sampling_methods = {
            'simple_random': self._simple_random_weights,
            'stratified': self._stratified_weights,
            'cluster': self._cluster_weights,
            'systematic': self._systematic_weights
        }
    
    def calculate_sampling_weights(self, responses: List[Dict], population_data: Dict, 
                                 sampling_method: str = 'simple_random') -> Dict:
        """
        Calculate sampling weights for survey responses
        Returns: dictionary with weights and metadata
        """
        try:
            if not responses:
                return {'weights': [], 'method': sampling_method, 'error': 'No responses provided'}
            
            # Get the appropriate weighting method
            weight_function = self.sampling_methods.get(sampling_method, self._simple_random_weights)
            
            # Calculate weights
            weights_result = weight_function(responses, population_data)
            
            # Add metadata
            weights_result.update({
                'method': sampling_method,
                'total_responses': len(responses),
                'effective_sample_size': self._calculate_effective_sample_size(weights_result['weights']),
                'weight_statistics': self._calculate_weight_statistics(weights_result['weights'])
            })
            
            return weights_result
            
        except Exception as e:
            logger.error(f"Error calculating sampling weights: {e}")
            return {'error': str(e), 'method': sampling_method}
    
    def _simple_random_weights(self, responses: List[Dict], population_data: Dict) -> Dict:
        """Calculate weights for simple random sampling"""
        n_responses = len(responses)
        
        # For simple random sampling, all weights are equal
        weights = [1.0] * n_responses
        
        return {
            'weights': weights,
            'weight_type': 'equal',
            'description': 'Equal weights for simple random sampling'
        }
    
    def _stratified_weights(self, responses: List[Dict], population_data: Dict) -> Dict:
        """Calculate weights for stratified sampling"""
        
        # Extract stratification variable (e.g., age group, region)
        strata_var = population_data.get('stratification_variable', 'region')
        population_proportions = population_data.get('population_proportions', {})
        
        if not population_proportions:
            # Fallback to equal weights
            return self._simple_random_weights(responses, population_data)
        
        # Count responses by strata
        strata_counts = defaultdict(int)
        response_strata = []
        
        for response in responses:
            response_data = response.get('data', {})
            stratum = response_data.get(strata_var, 'unknown')
            strata_counts[stratum] += 1
            response_strata.append(stratum)
        
        # Calculate weights
        weights = []
        total_responses = len(responses)
        
        for stratum in response_strata:
            if stratum in population_proportions and strata_counts[stratum] > 0:
                # Weight = (population proportion) / (sample proportion)
                pop_prop = population_proportions[stratum]
                sample_prop = strata_counts[stratum] / total_responses
                weight = pop_prop / sample_prop if sample_prop > 0 else 1.0
            else:
                weight = 1.0
            
            weights.append(weight)
        
        return {
            'weights': weights,
            'weight_type': 'stratified',
            'strata_counts': dict(strata_counts),
            'population_proportions': population_proportions,
            'description': f'Stratified weights based on {strata_var}'
        }
    
    def _cluster_weights(self, responses: List[Dict], population_data: Dict) -> Dict:
        """Calculate weights for cluster sampling"""
        
        cluster_var = population_data.get('cluster_variable', 'cluster_id')
        cluster_sizes = population_data.get('cluster_sizes', {})
        
        # Count responses by cluster
        cluster_counts = defaultdict(int)
        response_clusters = []
        
        for response in responses:
            response_data = response.get('data', {})
            cluster = response_data.get(cluster_var, 'unknown')
            cluster_counts[cluster] += 1
            response_clusters.append(cluster)
        
        # Calculate weights
        weights = []
        
        for cluster in response_clusters:
            if cluster in cluster_sizes and cluster_counts[cluster] > 0:
                # Weight based on cluster size and sampling rate
                cluster_size = cluster_sizes[cluster]
                responses_in_cluster = cluster_counts[cluster]
                weight = cluster_size / responses_in_cluster
            else:
                weight = 1.0
            
            weights.append(weight)
        
        return {
            'weights': weights,
            'weight_type': 'cluster',
            'cluster_counts': dict(cluster_counts),
            'cluster_sizes': cluster_sizes,
            'description': f'Cluster weights based on {cluster_var}'
        }
    
    def _systematic_weights(self, responses: List[Dict], population_data: Dict) -> Dict:
        """Calculate weights for systematic sampling"""
        
        # For systematic sampling, weights are typically equal unless there's bias
        sampling_interval = population_data.get('sampling_interval', 1)
        population_size = population_data.get('population_size', len(responses) * sampling_interval)
        
        # Calculate weight as population size / sample size
        weight = population_size / len(responses) if len(responses) > 0 else 1.0
        weights = [weight] * len(responses)
        
        return {
            'weights': weights,
            'weight_type': 'systematic',
            'sampling_interval': sampling_interval,
            'population_size': population_size,
            'description': 'Systematic sampling weights'
        }
    
    def _calculate_effective_sample_size(self, weights: List[float]) -> float:
        """Calculate effective sample size given weights"""
        if not weights:
            return 0.0
        
        sum_weights = sum(weights)
        sum_weights_squared = sum(w**2 for w in weights)
        
        if sum_weights_squared == 0:
            return 0.0
        
        return (sum_weights**2) / sum_weights_squared
    
    def _calculate_weight_statistics(self, weights: List[float]) -> Dict:
        """Calculate statistics about the weights"""
        if not weights:
            return {}
        
        weights_array = np.array(weights)
        
        return {
            'mean': float(np.mean(weights_array)),
            'median': float(np.median(weights_array)),
            'std': float(np.std(weights_array)),
            'min': float(np.min(weights_array)),
            'max': float(np.max(weights_array)),
            'cv': float(np.std(weights_array) / np.mean(weights_array)) if np.mean(weights_array) != 0 else 0
        }
    
    def estimate_population_parameters(self, responses: List[Dict], weights: List[float], 
                                     target_variables: List[str], confidence_level: str = '95%') -> Dict:
        """
        Estimate population parameters with confidence intervals
        """
        try:
            results = {}
            z_score = self.confidence_levels.get(confidence_level, 1.96)
            
            for variable in target_variables:
                var_result = self._estimate_variable_parameters(
                    responses, weights, variable, z_score, confidence_level
                )
                results[variable] = var_result
            
            return {
                'estimates': results,
                'confidence_level': confidence_level,
                'total_responses': len(responses),
                'effective_sample_size': self._calculate_effective_sample_size(weights)
            }
            
        except Exception as e:
            logger.error(f"Error estimating population parameters: {e}")
            return {'error': str(e)}
    
    def _estimate_variable_parameters(self, responses: List[Dict], weights: List[float], 
                                    variable: str, z_score: float, confidence_level: str) -> Dict:
        """Estimate parameters for a single variable"""
        
        # Extract variable values
        values = []
        var_weights = []
        
        for i, response in enumerate(responses):
            response_data = response.get('data', {})
            if variable in response_data:
                value = response_data[variable]
                if value is not None and value != '':
                    values.append(value)
                    var_weights.append(weights[i] if i < len(weights) else 1.0)
        
        if not values:
            return {'error': f'No valid values found for variable {variable}'}
        
        # Determine variable type and calculate appropriate estimates
        if all(isinstance(v, (int, float)) for v in values):
            return self._estimate_numeric_variable(values, var_weights, z_score, confidence_level)
        else:
            return self._estimate_categorical_variable(values, var_weights, z_score, confidence_level)
    
    def _estimate_numeric_variable(self, values: List[float], weights: List[float], 
                                 z_score: float, confidence_level: str) -> Dict:
        """Estimate parameters for numeric variable"""
        
        values_array = np.array(values)
        weights_array = np.array(weights)
        
        # Weighted mean
        weighted_mean = np.average(values_array, weights=weights_array)
        
        # Weighted variance
        weighted_variance = np.average((values_array - weighted_mean)**2, weights=weights_array)
        weighted_std = np.sqrt(weighted_variance)
        
        # Standard error of the mean
        effective_n = self._calculate_effective_sample_size(weights)
        standard_error = weighted_std / np.sqrt(effective_n) if effective_n > 0 else 0
        
        # Confidence interval
        margin_of_error = z_score * standard_error
        ci_lower = weighted_mean - margin_of_error
        ci_upper = weighted_mean + margin_of_error
        
        return {
            'variable_type': 'numeric',
            'estimate': float(weighted_mean),
            'standard_error': float(standard_error),
            'confidence_interval': {
                'lower': float(ci_lower),
                'upper': float(ci_upper),
                'level': confidence_level
            },
            'variance': float(weighted_variance),
            'standard_deviation': float(weighted_std),
            'sample_size': len(values),
            'effective_sample_size': float(effective_n)
        }
    
    def _estimate_categorical_variable(self, values: List[Any], weights: List[float], 
                                     z_score: float, confidence_level: str) -> Dict:
        """Estimate parameters for categorical variable"""
        
        # Count weighted frequencies
        category_weights = defaultdict(float)
        total_weight = sum(weights)
        
        for value, weight in zip(values, weights):
            category_weights[str(value)] += weight
        
        # Calculate proportions and confidence intervals
        category_estimates = {}
        
        for category, weight_sum in category_weights.items():
            proportion = weight_sum / total_weight if total_weight > 0 else 0
            
            # Standard error for proportion
            effective_n = self._calculate_effective_sample_size(weights)
            se_proportion = np.sqrt(proportion * (1 - proportion) / effective_n) if effective_n > 0 else 0
            
            # Confidence interval for proportion
            margin_of_error = z_score * se_proportion
            ci_lower = max(0, proportion - margin_of_error)
            ci_upper = min(1, proportion + margin_of_error)
            
            category_estimates[category] = {
                'proportion': float(proportion),
                'count': float(weight_sum),
                'standard_error': float(se_proportion),
                'confidence_interval': {
                    'lower': float(ci_lower),
                    'upper': float(ci_upper),
                    'level': confidence_level
                }
            }
        
        return {
            'variable_type': 'categorical',
            'categories': category_estimates,
            'total_responses': len(values),
            'effective_sample_size': float(self._calculate_effective_sample_size(weights))
        }
    
    def calculate_variance_estimates(self, responses: List[Dict], weights: List[float], 
                                   design_effect: float = 1.0) -> Dict:
        """
        Calculate variance estimates accounting for complex survey design
        """
        try:
            if not responses or not weights:
                return {'error': 'No responses or weights provided'}
            
            # Calculate design-based variance estimates
            effective_sample_size = self._calculate_effective_sample_size(weights)
            
            # Design effect adjustment
            adjusted_variance_factor = design_effect
            
            variance_info = {
                'design_effect': design_effect,
                'effective_sample_size': effective_sample_size,
                'nominal_sample_size': len(responses),
                'variance_inflation': design_effect,
                'adjusted_standard_errors': True
            }
            
            return variance_info
            
        except Exception as e:
            logger.error(f"Error calculating variance estimates: {e}")
            return {'error': str(e)}
    
    def perform_significance_tests(self, responses: List[Dict], weights: List[float], 
                                 test_specifications: List[Dict]) -> Dict:
        """
        Perform statistical significance tests
        """
        try:
            test_results = {}
            
            for test_spec in test_specifications:
                test_type = test_spec.get('type', 'chi_square')
                variables = test_spec.get('variables', [])
                test_name = test_spec.get('name', f'test_{len(test_results)}')
                
                if test_type == 'chi_square':
                    result = self._chi_square_test(responses, weights, variables)
                elif test_type == 't_test':
                    result = self._t_test(responses, weights, variables)
                elif test_type == 'mann_whitney':
                    result = self._mann_whitney_test(responses, weights, variables)
                else:
                    result = {'error': f'Unknown test type: {test_type}'}
                
                test_results[test_name] = result
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error performing significance tests: {e}")
            return {'error': str(e)}
    
    def _chi_square_test(self, responses: List[Dict], weights: List[float], variables: List[str]) -> Dict:
        """Perform chi-square test of independence"""
        
        if len(variables) != 2:
            return {'error': 'Chi-square test requires exactly 2 variables'}
        
        var1, var2 = variables
        
        # Extract data for both variables
        data_pairs = []
        pair_weights = []
        
        for i, response in enumerate(responses):
            response_data = response.get('data', {})
            if var1 in response_data and var2 in response_data:
                val1 = response_data[var1]
                val2 = response_data[var2]
                if val1 is not None and val2 is not None:
                    data_pairs.append((str(val1), str(val2)))
                    pair_weights.append(weights[i] if i < len(weights) else 1.0)
        
        if len(data_pairs) < 5:  # Minimum sample size for chi-square
            return {'error': 'Insufficient data for chi-square test'}
        
        # Create contingency table
        contingency_dict = defaultdict(lambda: defaultdict(float))
        
        for (val1, val2), weight in zip(data_pairs, pair_weights):
            contingency_dict[val1][val2] += weight
        
        # Convert to matrix
        val1_categories = sorted(contingency_dict.keys())
        val2_categories = sorted(set(val2 for val1_dict in contingency_dict.values() for val2 in val1_dict.keys()))
        
        contingency_matrix = []
        for val1 in val1_categories:
            row = []
            for val2 in val2_categories:
                row.append(contingency_dict[val1][val2])
            contingency_matrix.append(row)
        
        contingency_array = np.array(contingency_matrix)
        
        # Perform chi-square test
        try:
            chi2_stat, p_value, dof, expected = chi2_contingency(contingency_array)
            
            return {
                'test_type': 'chi_square',
                'variables': variables,
                'chi2_statistic': float(chi2_stat),
                'p_value': float(p_value),
                'degrees_of_freedom': int(dof),
                'significant': p_value < 0.05,
                'contingency_table': contingency_matrix,
                'row_labels': val1_categories,
                'column_labels': val2_categories
            }
            
        except Exception as e:
            return {'error': f'Chi-square test failed: {str(e)}'}
    
    def _t_test(self, responses: List[Dict], weights: List[float], variables: List[str]) -> Dict:
        """Perform t-test"""
        
        if len(variables) != 2:
            return {'error': 'T-test requires exactly 2 variables (grouping variable and numeric variable)'}
        
        group_var, numeric_var = variables
        
        # Extract data
        group1_values = []
        group2_values = []
        groups = set()
        
        for response in responses:
            response_data = response.get('data', {})
            if group_var in response_data and numeric_var in response_data:
                group = str(response_data[group_var])
                value = response_data[numeric_var]
                
                if isinstance(value, (int, float)):
                    groups.add(group)
                    if len(groups) <= 2:  # Only handle binary grouping
                        if group == sorted(groups)[0]:
                            group1_values.append(value)
                        else:
                            group2_values.append(value)
        
        if len(groups) != 2:
            return {'error': 'T-test requires exactly 2 groups'}
        
        if len(group1_values) < 3 or len(group2_values) < 3:
            return {'error': 'Insufficient data in one or both groups'}
        
        # Perform t-test
        try:
            t_stat, p_value = ttest_ind(group1_values, group2_values)
            
            return {
                'test_type': 't_test',
                'variables': variables,
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'group1_mean': float(np.mean(group1_values)),
                'group2_mean': float(np.mean(group2_values)),
                'group1_size': len(group1_values),
                'group2_size': len(group2_values)
            }
            
        except Exception as e:
            return {'error': f'T-test failed: {str(e)}'}
    
    def _mann_whitney_test(self, responses: List[Dict], weights: List[float], variables: List[str]) -> Dict:
        """Perform Mann-Whitney U test"""
        
        if len(variables) != 2:
            return {'error': 'Mann-Whitney test requires exactly 2 variables'}
        
        group_var, numeric_var = variables
        
        # Extract data (similar to t-test)
        group1_values = []
        group2_values = []
        groups = set()
        
        for response in responses:
            response_data = response.get('data', {})
            if group_var in response_data and numeric_var in response_data:
                group = str(response_data[group_var])
                value = response_data[numeric_var]
                
                if isinstance(value, (int, float)):
                    groups.add(group)
                    if len(groups) <= 2:
                        if group == sorted(groups)[0]:
                            group1_values.append(value)
                        else:
                            group2_values.append(value)
        
        if len(groups) != 2:
            return {'error': 'Mann-Whitney test requires exactly 2 groups'}
        
        if len(group1_values) < 3 or len(group2_values) < 3:
            return {'error': 'Insufficient data in one or both groups'}
        
        # Perform Mann-Whitney U test
        try:
            u_stat, p_value = mannwhitneyu(group1_values, group2_values, alternative='two-sided')
            
            return {
                'test_type': 'mann_whitney',
                'variables': variables,
                'u_statistic': float(u_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'group1_median': float(np.median(group1_values)),
                'group2_median': float(np.median(group2_values)),
                'group1_size': len(group1_values),
                'group2_size': len(group2_values)
            }
            
        except Exception as e:
            return {'error': f'Mann-Whitney test failed: {str(e)}'}

