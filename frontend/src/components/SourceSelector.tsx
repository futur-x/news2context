import { useState, useEffect } from 'react'
import { settingsAPI } from '../api/client'
import './SourceSelector.css'

interface Source {
    name: string
    hashid: string
    category: string
    url: string
}

interface SourceSelectorProps {
    selectedSources: string[]
    onChange: (sources: string[]) => void
    className?: string
}

export default function SourceSelector({ selectedSources, onChange, className = '' }: SourceSelectorProps) {
    const [sources, setSources] = useState<Source[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [filter, setFilter] = useState('')

    useEffect(() => {
        loadSources()
    }, [])

    const loadSources = async () => {
        try {
            const response = await settingsAPI.getTopHub()
            // Assuming response.data.sources is the list of sources
            // If the API returns the config object, we might need to access sources differently
            // Based on previous context, TopHub config usually has a 'sources' list
            setSources(response.data.sources || [])
        } catch (err) {
            console.error('Failed to load sources:', err)
            setError('Failed to load sources')
        } finally {
            setLoading(false)
        }
    }

    const toggleSource = (hashid: string) => {
        const newSelected = selectedSources.includes(hashid)
            ? selectedSources.filter(id => id !== hashid)
            : [...selectedSources, hashid]
        onChange(newSelected)
    }

    const filteredSources = sources.filter(source =>
        source.name.toLowerCase().includes(filter.toLowerCase()) ||
        source.category.toLowerCase().includes(filter.toLowerCase())
    )

    // Group sources by category
    const groupedSources = filteredSources.reduce((acc, source) => {
        if (!acc[source.category]) {
            acc[source.category] = []
        }
        acc[source.category].push(source)
        return acc
    }, {} as Record<string, Source[]>)

    if (loading) return <div className="source-selector-loading">Loading sources...</div>
    if (error) return <div className="source-selector-error">{error}</div>

    return (
        <div className={`source-selector ${className}`}>
            <div className="source-filter">
                <input
                    type="text"
                    placeholder="Filter sources..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="filter-input"
                />
            </div>

            <div className="sources-list">
                {Object.entries(groupedSources).map(([category, categorySources]) => (
                    <div key={category} className="source-category">
                        <h4 className="category-title">{category}</h4>
                        <div className="category-sources">
                            {categorySources.map(source => (
                                <div
                                    key={source.hashid}
                                    className={`source-item ${selectedSources.includes(source.hashid) ? 'selected' : ''}`}
                                    onClick={() => toggleSource(source.hashid)}
                                >
                                    <span className="source-name">{source.name}</span>
                                    {selectedSources.includes(source.hashid) && (
                                        <span className="check-icon">✓</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
                {filteredSources.length === 0 && (
                    <div className="no-results">No sources found</div>
                )}
            </div>
        </div>
    )
}
