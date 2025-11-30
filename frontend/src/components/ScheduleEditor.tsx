import { useState, useEffect } from 'react'
import { ScheduleConfig, cronToScheduleType, scheduleToCron, getNextRunTime, formatNextRun, validateCron, getDayName } from '../utils/scheduleUtils'
import './ScheduleEditor.css'

interface ScheduleEditorProps {
    enabled: boolean
    cron: string
    onSave: (enabled: boolean, cron: string) => Promise<void>
    onCancel: () => void
}

function ScheduleEditor({ enabled, cron, onSave, onCancel }: ScheduleEditorProps) {
    const [isEnabled, setIsEnabled] = useState(enabled)
    const [config, setConfig] = useState<ScheduleConfig>(cronToScheduleType(cron))
    const [saving, setSaving] = useState(false)
    const [customCron, setCustomCron] = useState(cron)
    const [cronError, setCronError] = useState('')

    // Update next run time when config changes
    const [nextRun, setNextRun] = useState<Date | null>(null)

    useEffect(() => {
        if (!isEnabled) {
            setNextRun(null)
            return
        }

        const cronExpr = config.type === 'custom' ? customCron : scheduleToCron(config)
        const next = getNextRunTime(cronExpr)
        setNextRun(next)
    }, [config, customCron, isEnabled])

    const handleSave = async () => {
        if (!isEnabled) {
            setSaving(true)
            await onSave(false, '')
            setSaving(false)
            return
        }

        const cronExpr = config.type === 'custom' ? customCron : scheduleToCron(config)

        if (!validateCron(cronExpr)) {
            setCronError('Invalid cron expression')
            return
        }

        setSaving(true)
        try {
            await onSave(true, cronExpr)
        } finally {
            setSaving(false)
        }
    }

    const handleTypeChange = (type: ScheduleConfig['type']) => {
        setCronError('')
        switch (type) {
            case 'disabled':
                setIsEnabled(false)
                setConfig({ type: 'disabled' })
                break
            case 'minutes':
                setIsEnabled(true)
                setConfig({ type: 'minutes', interval: 30 })
                break
            case 'hours':
                setIsEnabled(true)
                setConfig({ type: 'hours', interval: 2 })
                break
            case 'daily':
                setIsEnabled(true)
                setConfig({ type: 'daily', times: ['09:00'] })
                break
            case 'weekly':
                setIsEnabled(true)
                setConfig({ type: 'weekly', days: [1], time: '09:00' })
                break
            case 'custom':
                setIsEnabled(true)
                setConfig({ type: 'custom', cron: customCron })
                break
        }
    }

    const handleDayToggle = (day: number) => {
        if (config.type !== 'weekly') return
        const days = config.days || []
        const newDays = days.includes(day)
            ? days.filter(d => d !== day)
            : [...days, day].sort()
        setConfig({ ...config, days: newDays })
    }

    return (
        <div className="schedule-editor">
            <div className="schedule-type-selector">
                <label className="schedule-type-option">
                    <input
                        type="radio"
                        checked={!isEnabled}
                        onChange={() => handleTypeChange('disabled')}
                    />
                    <span>Disabled</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        checked={isEnabled && config.type === 'minutes'}
                        onChange={() => handleTypeChange('minutes')}
                    />
                    <span>Every</span>
                    {config.type === 'minutes' && (
                        <select
                            value={config.interval}
                            onChange={(e) => setConfig({ ...config, interval: parseInt(e.target.value) })}
                            className="inline-select"
                        >
                            <option value={5}>5</option>
                            <option value={15}>15</option>
                            <option value={30}>30</option>
                            <option value={60}>60</option>
                        </select>
                    )}
                    <span>minutes</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        checked={isEnabled && config.type === 'hours'}
                        onChange={() => handleTypeChange('hours')}
                    />
                    <span>Every</span>
                    {config.type === 'hours' && (
                        <select
                            value={config.interval}
                            onChange={(e) => setConfig({ ...config, interval: parseInt(e.target.value) })}
                            className="inline-select"
                        >
                            <option value={1}>1</option>
                            <option value={2}>2</option>
                            <option value={4}>4</option>
                            <option value={6}>6</option>
                            <option value={12}>12</option>
                        </select>
                    )}
                    <span>hours</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        checked={isEnabled && config.type === 'daily'}
                        onChange={() => handleTypeChange('daily')}
                    />
                    <span>Daily at</span>
                    {config.type === 'daily' && (
                        <input
                            type="time"
                            value={config.times?.[0] || '09:00'}
                            onChange={(e) => setConfig({ ...config, times: [e.target.value] })}
                            className="inline-time"
                        />
                    )}
                </label>

                <label className="schedule-type-option weekly-option">
                    <input
                        type="radio"
                        checked={isEnabled && config.type === 'weekly'}
                        onChange={() => handleTypeChange('weekly')}
                    />
                    <span>Weekly on</span>
                    {config.type === 'weekly' && (
                        <div className="weekly-config">
                            <div className="day-selector">
                                {[0, 1, 2, 3, 4, 5, 6].map(day => (
                                    <button
                                        key={day}
                                        type="button"
                                        className={`day-btn ${config.days?.includes(day) ? 'selected' : ''}`}
                                        onClick={() => handleDayToggle(day)}
                                    >
                                        {getDayName(day)}
                                    </button>
                                ))}
                            </div>
                            <div className="weekly-time">
                                <span>at</span>
                                <input
                                    type="time"
                                    value={config.time || '09:00'}
                                    onChange={(e) => setConfig({ ...config, time: e.target.value })}
                                    className="inline-time"
                                />
                            </div>
                        </div>
                    )}
                </label>

                <label className="schedule-type-option custom-option">
                    <input
                        type="radio"
                        checked={isEnabled && config.type === 'custom'}
                        onChange={() => handleTypeChange('custom')}
                    />
                    <span>Custom (Cron)</span>
                    {config.type === 'custom' && (
                        <input
                            type="text"
                            value={customCron}
                            onChange={(e) => {
                                setCustomCron(e.target.value)
                                setCronError('')
                            }}
                            placeholder="0 8 * * *"
                            className="inline-cron"
                        />
                    )}
                </label>
            </div>

            {cronError && (
                <div className="cron-error">{cronError}</div>
            )}

            {isEnabled && nextRun && (
                <div className="next-run-preview">
                    <span className="next-run-label">Next run:</span>
                    <span className="next-run-time">{formatNextRun(nextRun)}</span>
                </div>
            )}

            <div className="schedule-editor-actions">
                <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={onCancel}
                    disabled={saving}
                >
                    Cancel
                </button>
                <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSave}
                    disabled={saving}
                >
                    {saving ? 'Saving...' : 'Save Schedule'}
                </button>
            </div>
        </div>
    )
}

export default ScheduleEditor
