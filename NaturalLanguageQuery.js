import React, { useState, useRef, useEffect } from 'react';

const NaturalLanguageQuery = () => {
  const [query, setQuery] = useState('');
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    // Load previous queries
    const mockQueries = [
      {
        id: 1,
        query: "Show me the average satisfaction score by age group",
        sql: "SELECT age_group, AVG(satisfaction_score) as avg_satisfaction FROM survey_responses GROUP BY age_group",
        status: "completed",
        results: {
          data: [
            { age_group: "18-25", avg_satisfaction: 4.2 },
            { age_group: "26-35", avg_satisfaction: 4.5 },
            { age_group: "36-45", avg_satisfaction: 4.1 },
            { age_group: "46-55", avg_satisfaction: 4.3 },
            { age_group: "55+", avg_satisfaction: 4.4 }
          ],
          count: 5
        },
        timestamp: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 2,
        query: "What are the top 3 most common complaints?",
        sql: "SELECT complaint_category, COUNT(*) as frequency FROM feedback WHERE sentiment = 'negative' GROUP BY complaint_category ORDER BY frequency DESC LIMIT 3",
        status: "completed",
        results: {
          data: [
            { complaint_category: "Delivery Issues", frequency: 45 },
            { complaint_category: "Product Quality", frequency: 32 },
            { complaint_category: "Customer Service", frequency: 28 }
          ],
          count: 3
        },
        timestamp: new Date(Date.now() - 7200000).toISOString()
      },
      {
        id: 3,
        query: "How many responses were submitted last week?",
        sql: "SELECT COUNT(*) as total_responses FROM survey_responses WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK)",
        status: "completed",
        results: {
          data: [{ total_responses: 247 }],
          count: 1
        },
        timestamp: new Date(Date.now() - 10800000).toISOString()
      }
    ];
    setQueries(mockQueries);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    
    // Create new query object
    const newQuery = {
      id: Date.now(),
      query: query.trim(),
      status: "processing",
      timestamp: new Date().toISOString()
    };

    setQueries(prev => [newQuery, ...prev]);
    setQuery('');

    // Simulate API call
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock SQL generation and results
      const mockSQL = generateMockSQL(query);
      const mockResults = generateMockResults(query);
      
      setQueries(prev => prev.map(q => 
        q.id === newQuery.id 
          ? { ...q, sql: mockSQL, results: mockResults, status: "completed" }
          : q
      ));
    } catch (error) {
      setQueries(prev => prev.map(q => 
        q.id === newQuery.id 
          ? { ...q, status: "failed", error: "Failed to process query" }
          : q
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockSQL = (query) => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('average') || lowerQuery.includes('avg')) {
      return "SELECT category, AVG(score) as average_score FROM survey_responses GROUP BY category";
    } else if (lowerQuery.includes('count') || lowerQuery.includes('how many')) {
      return "SELECT COUNT(*) as total_count FROM survey_responses WHERE condition = 'value'";
    } else if (lowerQuery.includes('top') || lowerQuery.includes('most')) {
      return "SELECT item, COUNT(*) as frequency FROM data_table GROUP BY item ORDER BY frequency DESC LIMIT 5";
    } else {
      return "SELECT * FROM survey_responses WHERE relevant_condition = 'value' ORDER BY created_at DESC";
    }
  };

  const generateMockResults = (query) => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('average') || lowerQuery.includes('avg')) {
      return {
        data: [
          { category: "Product", average_score: 4.2 },
          { category: "Service", average_score: 4.5 },
          { category: "Support", average_score: 4.1 }
        ],
        count: 3
      };
    } else if (lowerQuery.includes('count') || lowerQuery.includes('how many')) {
      return {
        data: [{ total_count: Math.floor(Math.random() * 1000) + 100 }],
        count: 1
      };
    } else {
      return {
        data: Array.from({ length: 5 }, (_, i) => ({
          id: i + 1,
          value: `Sample data ${i + 1}`,
          score: Math.floor(Math.random() * 5) + 1
        })),
        count: 5
      };
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit(e);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes} minutes ago`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)} hours ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Natural Language Query</h1>
        <p className="text-gray-600">Ask questions about your data in plain English</p>
      </div>

      {/* Query Input */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Ask a question about your data
            </label>
            <textarea
              ref={textareaRef}
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., What is the average satisfaction score by region? How many responses did we get last month?"
              className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="3"
              disabled={isLoading}
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Press Ctrl+Enter to submit or click the button
            </p>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                'Ask Question'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Query History */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900">Query History</h2>
        
        {queries.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No queries yet</p>
            <p className="text-sm">Ask your first question above to get started</p>
          </div>
        ) : (
          queries.map((queryItem) => (
            <QueryCard
              key={queryItem.id}
              query={queryItem}
              isSelected={selectedQuery?.id === queryItem.id}
              onSelect={() => setSelectedQuery(queryItem)}
              formatTimestamp={formatTimestamp}
            />
          ))
        )}
      </div>
    </div>
  );
};

const QueryCard = ({ query, isSelected, onSelect, formatTimestamp }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div 
      className={`bg-white rounded-lg shadow border-2 cursor-pointer transition-all ${
        isSelected ? 'border-blue-500' : 'border-transparent hover:border-gray-200'
      }`}
      onClick={onSelect}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 mb-2">{query.query}</h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>{formatTimestamp(query.timestamp)}</span>
              <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(query.status)}`}>
                {query.status}
              </span>
            </div>
          </div>
          {query.status === 'processing' && (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          )}
        </div>

        {query.sql && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Generated SQL:</h4>
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
              <code>{query.sql}</code>
            </pre>
          </div>
        )}

        {query.results && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              Results ({query.results.count} {query.results.count === 1 ? 'row' : 'rows'}):
            </h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {query.results.data.length > 0 && Object.keys(query.results.data[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {key.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {query.results.data.map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).map((value, cellIndex) => (
                        <td key={cellIndex} className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                          {typeof value === 'number' ? value.toLocaleString() : value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {query.error && (
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <p className="text-sm text-red-600">{query.error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NaturalLanguageQuery;

