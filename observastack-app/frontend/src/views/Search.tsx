import React, { useState } from 'react'
import { SearchForm, SearchResults, SearchHistory } from '../components/search'
import { useSearch, useCrossSignalNavigation } from '../hooks'
import { SearchQuery, SearchItem } from '../types'

export default function Search() {
  const [showHistory, setShowHistory] = useState(false)
  const { 
    results, 
    loading, 
    error, 
    search, 
    getSearchHistory, 
    saveSearch, 
    deleteFromHistory 
  } = useSearch({ enableHistory: true })
  
  const { navigateToCorrelatedData } = useCrossSignalNavigation()

  const handleSearch = (query: SearchQuery) => {
    search(query, true) // immediate search
    setShowHistory(false) // hide history when searching
  }

  const handleResultClick = (item: SearchItem) => {
    // Handle result click - could open detail view, copy to clipboard, etc.
    console.log('Result clicked:', item)
  }

  const handleCorrelationClick = async (correlationId: string) => {
    try {
      // Navigate to correlated traces/logs
      const correlatedResults = await navigateToCorrelatedData(correlationId, 'traces')
      console.log('Correlated results:', correlatedResults)
    } catch (error) {
      console.error('Failed to find correlated data:', error)
    }
  }

  const handleHistorySelect = (query: SearchQuery) => {
    search(query, true)
    setShowHistory(false)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Unified Search</h1>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            {showHistory ? 'Hide History' : 'Show History'}
          </button>
        </div>
        <p className="text-gray-600">
          Search across logs, metrics, and traces from a single interface
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Search Form */}
          <SearchForm
            onSearch={handleSearch}
            loading={loading}
          />

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Search Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {error.message}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Search Results */}
          {(results || loading) && (
            <SearchResults
              results={results || { items: [], stats: { matched: 0, scanned: 0, latencyMs: 0, sources: {} }, facets: [] }}
              loading={loading}
              onResultClick={handleResultClick}
              onCorrelationClick={handleCorrelationClick}
            />
          )}
        </div>

        {/* Search History Sidebar */}
        {showHistory && (
          <div className="lg:col-span-1">
            <SearchHistory
              onSelectQuery={handleHistorySelect}
              onSaveQuery={saveSearch}
              onDeleteQuery={deleteFromHistory}
            />
          </div>
        )}
      </div>
    </div>
  )
}
