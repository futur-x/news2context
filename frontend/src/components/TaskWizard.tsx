import { useState } from 'react'
import { taskAPI, sourcesAPI } from '../api/client'
import SourceSelector from './SourceSelector'
import './TaskWizard.css'

interface TaskWizardProps {
    onClose: () => void
    onSuccess: (taskName: string) => void
}

interface WizardData {
    name: string
    scene: string
    maxSources: number
    sources: string[]
    recommendedSources: any[]
    dateRange: string
    cron: string
    runImmediately: boolean
}

export default function TaskWizard({ onClose, onSuccess }: TaskWizardProps) {
    const [step, setStep] = useState(1)
    const [loading, setLoading] = useState(false)
    const [wizardData, setWizardData] = useState<WizardData>({
        name: '',
        scene: '',
        maxSources: 10,
        sources: [],
        recommendedSources: [],
        dateRange: 'last_1_days',
        cron: '0 8 * * *',
        runImmediately: false
    })

    const handleNext = async () => {
        if (step === 1) {
            // Validate Step 1
            if (!wizardData.name || !wizardData.scene) {
                alert('Please fill in task name and scene description')
                return
            }
            // Validate task name format (only alphanumeric, underscore, hyphen)
            const namePattern = /^[a-zA-Z0-9_-]+$/
            if (!namePattern.test(wizardData.name)) {
                alert('Task name can only contain English letters, numbers, underscores (_), and hyphens (-)')
                return
            }
            // Trigger AI recommendation
            await handleRecommend()
        } else if (step === 2) {
            // Proceed to manual selection
            setStep(3)
        } else if (step === 3) {
            // Proceed to configuration
            setStep(4)
        } else if (step === 4) {
            // Create task
            await handleCreateTask()
        }
    }

    const handleBack = () => {
        if (step > 1) setStep(step - 1)
    }

    const handleRecommend = async () => {
        setLoading(true)
        try {
            const res = await sourcesAPI.recommend(wizardData.scene, wizardData.maxSources)
            const recommended = res.data.recommended_sources
            setWizardData({
                ...wizardData,
                recommendedSources: recommended,
                sources: recommended.map((s: any) => s.hashid)
            })
            setStep(2)
        } catch (err) {
            console.error('Recommendation failed:', err)
            alert('AI recommendation failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const handleRemoveRecommended = (hashidToRemove: string) => {
        setWizardData({
            ...wizardData,
            recommendedSources: wizardData.recommendedSources.filter(s => (s.hashid || s.id) !== hashidToRemove),
            sources: wizardData.sources.filter(id => id !== hashidToRemove)
        })
    }

    const handleCreateTask = async () => {
        setLoading(true)
        try {
            // Fetch source details
            const allSourcesRes = await sourcesAPI.list()
            const allSources = allSourcesRes.data || []

            // Combine all available sources (saved + recommended)
            const availableSources = [...allSources, ...wizardData.recommendedSources]

            // Deduplicate
            const uniqueSourcesMap = new Map(availableSources.map((s: any) => [s.hashid, s]))

            const selectedSourceObjects = wizardData.sources
                .map(id => uniqueSourcesMap.get(id))
                .filter(s => s) // Filter out undefined
                .map((s: any) => ({
                    name: s.name,
                    hashid: s.hashid || s.id,
                    category: s.category,
                    url: s.url
                }))

            await taskAPI.create({
                name: wizardData.name,
                scene: wizardData.scene,
                sources: selectedSourceObjects,
                date_range: wizardData.dateRange,
                cron: wizardData.cron,
                engine_name: 'tophub'
            })

            // Run immediately if requested
            if (wizardData.runImmediately) {
                await taskAPI.run(wizardData.name)
            }

            onSuccess(wizardData.name)
            onClose()
        } catch (error) {
            console.error('Failed to create task:', error)
            alert('Failed to create task')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="wizard-overlay" onClick={onClose}>
            <div className="wizard-modal" onClick={(e) => e.stopPropagation()}>
                <div className="wizard-header">
                    <h2>Create New Knowledge Base</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="wizard-steps">
                    <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                        <div className="step-number">1</div>
                        <div className="step-label">Scene</div>
                    </div>
                    <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                        <div className="step-number">2</div>
                        <div className="step-label">AI Recommend</div>
                    </div>
                    <div className={`step ${step >= 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}>
                        <div className="step-number">3</div>
                        <div className="step-label">Adjust Sources</div>
                    </div>
                    <div className={`step ${step >= 4 ? 'active' : ''}`}>
                        <div className="step-number">4</div>
                        <div className="step-label">Configure</div>
                    </div>
                </div>

                <div className="wizard-content">
                    {step === 1 && (
                        <div className="wizard-step">
                            <h3>Describe Your Scenario</h3>
                            <div className="form-group">
                                <label>Task Name *</label>
                                <input
                                    type="text"
                                    placeholder="e.g., tech-news, finance_daily, ai-research"
                                    value={wizardData.name}
                                    onChange={(e) => setWizardData({ ...wizardData, name: e.target.value })}
                                />
                                <small style={{ color: '#888', fontSize: '0.85em' }}>
                                    Only English letters, numbers, underscores (_), and hyphens (-) are allowed
                                </small>
                            </div>
                            <div className="form-group">
                                <label>Scene Description *</label>
                                <textarea
                                    rows={4}
                                    placeholder="e.g., I'm a fund manager focusing on macroeconomics, financial markets, and policy regulations..."
                                    value={wizardData.scene}
                                    onChange={(e) => setWizardData({ ...wizardData, scene: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Number of Sources</label>
                                <input
                                    type="number"
                                    min="5"
                                    max="30"
                                    value={wizardData.maxSources}
                                    onChange={(e) => setWizardData({ ...wizardData, maxSources: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="wizard-step">
                            <h3>AI Recommended Sources</h3>
                            <p className="step-description">
                                Based on your scenario, we recommend the following {wizardData.recommendedSources.length} sources:
                            </p>
                            <div className="recommended-sources">
                                {wizardData.recommendedSources.map((source: any) => (
                                    <div key={source.hashid} className="recommended-source-card">
                                        <div className="source-info">
                                            <div className="source-name">{source.name}</div>
                                            <div className="source-category">{source.category}</div>
                                            {source.reason && (
                                                <div className="source-reason">💡 {source.reason}</div>
                                            )}
                                        </div>
                                        <button
                                            className="btn-icon remove-btn"
                                            onClick={() => handleRemoveRecommended(source.hashid)}
                                            title="Remove this source"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="wizard-step">
                            <h3>Adjust Sources (Optional)</h3>
                            <p className="step-description">
                                You can add or remove sources manually. Currently selected: {wizardData.sources.length}
                            </p>
                            <SourceSelector
                                selectedSources={wizardData.sources}
                                onChange={(sources) => setWizardData({ ...wizardData, sources })}
                                scene={wizardData.scene}
                            />
                        </div>
                    )}

                    {step === 4 && (
                        <div className="wizard-step">
                            <h3>Configuration & Confirmation</h3>

                            <div className="form-group">
                                <label>Date Range</label>
                                <div className="radio-group">
                                    {[
                                        { value: 'last_1_days', label: 'Last 1 Day' },
                                        { value: 'last_2_days', label: 'Last 2 Days' },
                                        { value: 'last_3_days', label: 'Last 3 Days' },
                                        { value: 'last_7_days', label: 'Last 7 Days' }
                                    ].map(option => (
                                        <label key={option.value} className="radio-label">
                                            <input
                                                type="radio"
                                                name="dateRange"
                                                value={option.value}
                                                checked={wizardData.dateRange === option.value}
                                                onChange={(e) => setWizardData({ ...wizardData, dateRange: e.target.value })}
                                            />
                                            {option.label}
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Schedule (Cron)</label>
                                <input
                                    type="text"
                                    value={wizardData.cron}
                                    onChange={(e) => setWizardData({ ...wizardData, cron: e.target.value })}
                                />
                                <small>Default: Daily at 8:00 AM</small>
                            </div>

                            <div className="form-group">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={wizardData.runImmediately}
                                        onChange={(e) => setWizardData({ ...wizardData, runImmediately: e.target.checked })}
                                    />
                                    Run collection immediately after creation
                                </label>
                            </div>

                            <div className="task-summary">
                                <h4>Summary</h4>
                                <div className="summary-item">
                                    <strong>Task Name:</strong> {wizardData.name}
                                </div>
                                <div className="summary-item">
                                    <strong>Scene:</strong> {wizardData.scene.substring(0, 100)}...
                                </div>
                                <div className="summary-item">
                                    <strong>Sources:</strong> {wizardData.sources.length} selected
                                </div>
                                <div className="summary-item">
                                    <strong>Date Range:</strong> {wizardData.dateRange.replace('last_', '').replace('_days', ' days')}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="wizard-footer">
                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={step === 1 ? onClose : handleBack}
                        disabled={loading}
                    >
                        {step === 1 ? 'Cancel' : 'Back'}
                    </button>
                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={handleNext}
                        disabled={loading}
                    >
                        {loading ? 'Processing...' : step === 4 ? 'Create Task' : 'Next'}
                    </button>
                </div>
            </div>
        </div>
    )
}
