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
            const allSources = response.data || []

            // 去重：使用 Map 来确保每个 hashid 只出现一次
            const uniqueSourcesMap = new Map()
            allSources.forEach((source: Source) => {
                if (!uniqueSourcesMap.has(source.hashid)) {
                    uniqueSourcesMap.set(source.hashid, source)
                }
            })

            setSources(Array.from(uniqueSourcesMap.values()))
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
            return  // Silently return if no scene
        }
        setRecommending(true)
        try {
            const res = await sourcesAPI.recommend(scene)
            const recommended = res.data.recommended_sources
            const recommendedIds = recommended.map((s: any) => s.hashid)

            // Merge with existing selection
            const newSelection = Array.from(new Set([...selectedSources, ...recommendedIds]))
            onChange(newSelection)
        } catch (err) {
            console.error('Recommendation failed:', err)
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

    // Sort sources within each category: selected first, then unselected
    Object.keys(groupedSources).forEach(category => {
        groupedSources[category].sort((a, b) => {
            const aSelected = selectedSources.includes(a.hashid)
            const bSelected = selectedSources.includes(b.hashid)
            if (aSelected && !bSelected) return -1
            if (!aSelected && bSelected) return 1
            return 0
        })
    })

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
                        className="btn btn-secondary ai-recommend-btn"
                        onClick={handleRecommend}
                        disabled={!scene || recommending}
                        title="AI 推荐新闻源"
                    >
                        <span className="btn-icon">✨</span>
                        <span className="btn-text">{recommending ? 'AI 推荐中...' : 'AI 推荐'}</span>
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
