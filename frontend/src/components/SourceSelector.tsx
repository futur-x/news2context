import { useState, useEffect } from 'react'
import { sourcesAPI } from '../api/client'
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
    scene?: string
}

export default function SourceSelector({ selectedSources, onChange, className = '', scene }: SourceSelectorProps) {
    const [sources, setSources] = useState<Source[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [filter, setFilter] = useState('')
    const [recommending, setRecommending] = useState(false)

    useEffect(() => {
        loadSources()
    }, [])

    const loadSources = async () => {
        try {
            const response = await sourcesAPI.list()
            setSources(response.data || [])
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

    const handleRecommend = async () => {
        if (!scene) {
            alert('Please enter a scene description first.')
            return
        }
        setRecommending(true)
        try {
            const res = await sourcesAPI.recommend(scene)
            const recommended = res.data.recommended_sources
            const recommendedIds = recommended.map((s: any) => s.hashid)

            // Merge with existing selection
            const newSelection = Array.from(new Set([...selectedSources, ...recommendedIds]))
            onChange(newSelection)

            alert(`✨ AI recommended ${recommended.length} sources for "${scene}"`)
        } catch (err) {
            console.error('Recommendation failed:', err)
            alert('AI recommendation failed')
        } finally {
            setRecommending(false)
        }
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
            <div className="source-toolbar">
                <div className="source-filter">
                    <input
                        type="text"
                        placeholder="Filter sources..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="filter-input"
                    />
                </div>
                {scene && (
                    <button
                        className="btn btn-sm btn-outline ai-recommend-btn"
                        onClick={handleRecommend}
                        disabled={recommending}
                        title={`Recommend sources for scene: ${scene}`}
                    >
                        {recommending ? 'Thinking...' : '✨ AI Recommend'}
                    </button>
                )}
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
