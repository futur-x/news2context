import { useState, useEffect, useRef } from 'react'
import './ScheduleEditor.css'

interface ScheduleConfig {
    enabled: boolean
    cron: string
}

interface ScheduleEditorProps {
    schedule: ScheduleConfig
    onChange: (schedule: ScheduleConfig) => void
    onSave?: () => void
    onCancel?: () => void
}

type ScheduleType = 'disabled' | 'interval' | 'daily' | 'weekly' | 'custom'

function ScheduleEditor({ schedule, onChange, onSave, onCancel }: ScheduleEditorProps) {
    const [scheduleType, setScheduleType] = useState<ScheduleType>('disabled')
    const [intervalValue, setIntervalValue] = useState(30)
    const [intervalUnit, setIntervalUnit] = useState<'minutes' | 'hours'>('minutes')
    const [dailyTimes, setDailyTimes] = useState<string[]>(['09:00'])
    const [weeklyDays, setWeeklyDays] = useState<number[]>([1]) // 1 = Monday
    const [weeklyTime, setWeeklyTime] = useState('09:00')
    const [customCron, setCustomCron] = useState('0 9 * * *')

    // Track if this is the first render to skip initial onChange
    const skipNextOnChange = useRef(true)
    const lastScheduleRef = useRef(schedule)

    // Parse existing cron on mount or when schedule changes
    useEffect(() => {
        // Only parse if schedule actually changed
        if (schedule.enabled === lastScheduleRef.current.enabled &&
            schedule.cron === lastScheduleRef.current.cron) {
            return
        }

        lastScheduleRef.current = schedule

        // Mark that we should skip the next onChange call (from state updates below)
        skipNextOnChange.current = true

        if (!schedule.enabled) {
            setScheduleType('disabled')
            return
        }

        const cron = schedule.cron
        setCustomCron(cron)

        // Try to detect schedule type from cron
        if (cron.match(/^\*\/\d+ \* \* \* \*$/)) {
            // Interval minutes: */30 * * * *
            const minutes = parseInt(cron.split('/')[1].split(' ')[0])
            setScheduleType('interval')
            setIntervalValue(minutes)
            setIntervalUnit('minutes')
        } else if (cron.match(/^0 \*\/\d+ \* \* \*$/)) {
            // Interval hours: 0 */2 * * *
            const hours = parseInt(cron.split('/')[1].split(' ')[0])
            setScheduleType('interval')
            setIntervalValue(hours)
            setIntervalUnit('hours')
        } else if (cron.match(/^0 \d+(,\d+)* \* \* \*$/)) {
            // Daily: 0 9,14,18 * * *
            const hours = cron.split(' ')[1].split(',')
            const times = hours.map(h => `${h.padStart(2, '0')}:00`)
            setScheduleType('daily')
            setDailyTimes(times)
        } else if (cron.match(/^0 \d+ \* \* \d+(,\d+)*$/)) {
            // Weekly: 0 9 * * 1,3,5
            const hour = cron.split(' ')[1]
            const days = cron.split(' ')[4].split(',').map(d => parseInt(d))
            setScheduleType('weekly')
            setWeeklyTime(`${hour.padStart(2, '0')}:00`)
            setWeeklyDays(days)
        } else {
            setScheduleType('custom')
        }
    }, [schedule])

    // Generate cron expression based on current settings
    const generateCron = (): string => {
        switch (scheduleType) {
            case 'disabled':
                return '0 9 * * *' // Default
            case 'interval':
                if (intervalUnit === 'minutes') {
                    return `*/${intervalValue} * * * *`
                } else {
                    return `0 */${intervalValue} * * *`
                }
            case 'daily':
                const hours = dailyTimes.map(t => parseInt(t.split(':')[0])).join(',')
                return `0 ${hours} * * *`
            case 'weekly':
                const hour = parseInt(weeklyTime.split(':')[0])
                const days = weeklyDays.join(',')
                return `0 ${hour} * * ${days}`
            case 'custom':
                return customCron
            default:
                return '0 9 * * *'
        }
    }

    // Update parent when settings change
    useEffect(() => {
        // Skip the onChange call that results from parsing the initial prop
        if (skipNextOnChange.current) {
            skipNextOnChange.current = false
            return
        }

        const newCron = generateCron()

        const newSchedule: ScheduleConfig = {
            enabled: scheduleType !== 'disabled',
            cron: newCron
        }
        onChange(newSchedule)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [scheduleType, intervalValue, intervalUnit, dailyTimes, weeklyDays, weeklyTime, customCron])

    const addDailyTime = () => {
        setDailyTimes([...dailyTimes, '12:00'])
    }

    const removeDailyTime = (index: number) => {
        setDailyTimes(dailyTimes.filter((_, i) => i !== index))
    }

    const updateDailyTime = (index: number, value: string) => {
        const newTimes = [...dailyTimes]
        newTimes[index] = value
        setDailyTimes(newTimes)
    }

    const toggleWeeklyDay = (day: number) => {
        if (weeklyDays.includes(day)) {
            setWeeklyDays(weeklyDays.filter(d => d !== day))
        } else {
            setWeeklyDays([...weeklyDays, day].sort())
        }
    }

    const weekDays = [
        { value: 1, label: 'Mon' },
        { value: 2, label: 'Tue' },
        { value: 3, label: 'Wed' },
        { value: 4, label: 'Thu' },
        { value: 5, label: 'Fri' },
        { value: 6, label: 'Sat' },
        { value: 0, label: 'Sun' }
    ]

    const getNextRunPreview = (): string => {
        if (scheduleType === 'disabled') {
            return 'Disabled - will not run automatically'
        }

        const cron = generateCron()
        // Simple preview - in production, use a cron parser library
        if (scheduleType === 'interval') {
            return `Every ${intervalValue} ${intervalUnit}`
        } else if (scheduleType === 'daily') {
            return `Daily at ${dailyTimes.join(', ')}`
        } else if (scheduleType === 'weekly') {
            const dayNames = weeklyDays.map(d => weekDays.find(wd => wd.value === d)?.label).join(', ')
            return `Weekly on ${dayNames} at ${weeklyTime}`
        } else {
            return `Cron: ${cron}`
        }
    }

    return (
        <div className="schedule-editor">
            <div className="schedule-type-selector">
                <label className="schedule-type-option">
                    <input
                        type="radio"
                        name="scheduleType"
                        checked={scheduleType === 'disabled'}
                        onChange={() => setScheduleType('disabled')}
                    />
                    <span>Disabled</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        name="scheduleType"
                        checked={scheduleType === 'interval'}
                        onChange={() => setScheduleType('interval')}
                    />
                    <span>Every</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        name="scheduleType"
                        checked={scheduleType === 'daily'}
                        onChange={() => setScheduleType('daily')}
                    />
                    <span>Daily</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        name="scheduleType"
                        checked={scheduleType === 'weekly'}
                        onChange={() => setScheduleType('weekly')}
                    />
                    <span>Weekly</span>
                </label>

                <label className="schedule-type-option">
                    <input
                        type="radio"
                        name="scheduleType"
                        checked={scheduleType === 'custom'}
                        onChange={() => setScheduleType('custom')}
                    />
                    <span>Custom</span>
                </label>
            </div>

            <div className="schedule-config">
                {scheduleType === 'interval' && (
                    <div className="interval-config">
                        <input
                            type="number"
                            min="1"
                            max="1440"
                            value={intervalValue}
                            onChange={(e) => setIntervalValue(parseInt(e.target.value) || 1)}
                            className="interval-input"
                        />
                        <select
                            value={intervalUnit}
                            onChange={(e) => setIntervalUnit(e.target.value as 'minutes' | 'hours')}
                            className="interval-unit"
                        >
                            <option value="minutes">minutes</option>
                            <option value="hours">hours</option>
                        </select>
                    </div>
                )}

                {scheduleType === 'daily' && (
                    <div className="daily-config">
                        <div className="time-list">
                            {dailyTimes.map((time, index) => (
                                <div key={index} className="time-item">
                                    <input
                                        type="time"
                                        value={time}
                                        onChange={(e) => updateDailyTime(index, e.target.value)}
                                    />
                                    {dailyTimes.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeDailyTime(index)}
                                            className="btn-remove-time"
                                        >
                                            ×
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                        <button
                            type="button"
                            onClick={addDailyTime}
                            className="btn btn-secondary btn-sm"
                        >
                            + Add Time
                        </button>
                    </div>
                )}

                {scheduleType === 'weekly' && (
                    <div className="weekly-config">
                        <div className="weekday-selector">
                            {weekDays.map(day => (
                                <label key={day.value} className={`weekday-btn ${weeklyDays.includes(day.value) ? 'selected' : ''}`}>
                                    <input
                                        type="checkbox"
                                        checked={weeklyDays.includes(day.value)}
                                        onChange={() => toggleWeeklyDay(day.value)}
                                    />
                                    <span>{day.label}</span>
                                </label>
                            ))}
                        </div>
                        <div className="weekly-time">
                            <label>at</label>
                            <input
                                type="time"
                                value={weeklyTime}
                                onChange={(e) => setWeeklyTime(e.target.value)}
                            />
                        </div>
                    </div>
                )}

                {scheduleType === 'custom' && (
                    <div className="custom-config">
                        <input
                            type="text"
                            value={customCron}
                            onChange={(e) => setCustomCron(e.target.value)}
                            placeholder="0 9 * * *"
                            className="cron-input"
                        />
                        <small>Cron expression (minute hour day month weekday)</small>
                    </div>
                )}
            </div>

            <div className="schedule-preview">
                <strong>Schedule:</strong> {getNextRunPreview()}
            </div>

            {(onSave || onCancel) && (
                <div className="schedule-actions">
                    {onCancel && (
                        <button type="button" onClick={onCancel} className="btn btn-secondary">
                            Cancel
                        </button>
                    )}
                    {onSave && (
                        <button type="button" onClick={onSave} className="btn btn-primary">
                            Save Schedule
                        </button>
                    )}
                </div>
            )}
        </div>
    )
}

export default ScheduleEditor
