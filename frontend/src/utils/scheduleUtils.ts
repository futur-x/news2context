// Schedule utility functions for cron expression handling

export interface ScheduleConfig {
    type: 'disabled' | 'minutes' | 'hours' | 'daily' | 'weekly' | 'custom'
    interval?: number  // For minutes/hours
    times?: string[]   // For daily (e.g., ['09:00', '14:00'])
    days?: number[]    // For weekly (0=Sun, 1=Mon, ..., 6=Sat)
    time?: string      // For weekly (e.g., '09:00')
    cron?: string      // For custom
}

/**
 * Parse cron expression to schedule config
 */
export function cronToScheduleType(cron: string): ScheduleConfig {
    if (!cron || cron === '') {
        return { type: 'disabled' }
    }

    const parts = cron.trim().split(/\s+/)
    if (parts.length !== 5) {
        return { type: 'custom', cron }
    }

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

    // Every X minutes: */X * * * *
    if (minute.startsWith('*/') && hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
        const interval = parseInt(minute.substring(2))
        return { type: 'minutes', interval }
    }

    // Every X hours: 0 */X * * *
    if (minute === '0' && hour.startsWith('*/') && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
        const interval = parseInt(hour.substring(2))
        return { type: 'hours', interval }
    }

    // Daily at specific times: M H * * *
    if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*' && !minute.includes('*') && !hour.includes('*')) {
        // Single time
        const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
        return { type: 'daily', times: [time] }
    }

    // Weekly: M H * * D
    if (dayOfMonth === '*' && month === '*' && dayOfWeek !== '*' && !minute.includes('*') && !hour.includes('*')) {
        const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
        const days = dayOfWeek.split(',').map(d => parseInt(d))
        return { type: 'weekly', days, time }
    }

    // Default to custom
    return { type: 'custom', cron }
}

/**
 * Convert schedule config to cron expression
 */
export function scheduleToCron(config: ScheduleConfig): string {
    switch (config.type) {
        case 'disabled':
            return ''

        case 'minutes':
            return `*/${config.interval} * * * *`

        case 'hours':
            return `0 */${config.interval} * * *`

        case 'daily':
            if (!config.times || config.times.length === 0) {
                return '0 8 * * *'  // Default to 8:00 AM
            }
            // For multiple times, we'll use the first one
            // (Cron doesn't support multiple times natively)
            const [hour, minute] = config.times[0].split(':')
            return `${minute} ${hour} * * *`

        case 'weekly':
            if (!config.days || config.days.length === 0 || !config.time) {
                return '0 8 * * 1'  // Default to Monday 8:00 AM
            }
            const [h, m] = config.time.split(':')
            const daysStr = config.days.sort().join(',')
            return `${m} ${h} * * ${daysStr}`

        case 'custom':
            return config.cron || '0 8 * * *'

        default:
            return '0 8 * * *'
    }
}

/**
 * Calculate next run time from cron expression
 * This is a simplified version - for production, use a library like cron-parser
 */
export function getNextRunTime(cron: string): Date | null {
    if (!cron || cron === '') {
        return null
    }

    const now = new Date()
    const parts = cron.trim().split(/\s+/)

    if (parts.length !== 5) {
        return null
    }

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

    // Simple calculation for common patterns
    const next = new Date(now)

    // Every X minutes
    if (minute.startsWith('*/')) {
        const interval = parseInt(minute.substring(2))
        const currentMinute = now.getMinutes()
        const nextMinute = Math.ceil(currentMinute / interval) * interval
        next.setMinutes(nextMinute)
        next.setSeconds(0)
        next.setMilliseconds(0)
        if (nextMinute >= 60) {
            next.setHours(next.getHours() + 1)
            next.setMinutes(nextMinute - 60)
        }
        return next
    }

    // Every X hours
    if (hour.startsWith('*/') && minute === '0') {
        const interval = parseInt(hour.substring(2))
        const currentHour = now.getHours()
        const nextHour = Math.ceil(currentHour / interval) * interval
        next.setHours(nextHour)
        next.setMinutes(0)
        next.setSeconds(0)
        next.setMilliseconds(0)
        if (nextHour >= 24) {
            next.setDate(next.getDate() + 1)
            next.setHours(nextHour - 24)
        }
        return next
    }

    // Daily at specific time
    if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
        const targetHour = parseInt(hour)
        const targetMinute = parseInt(minute)
        next.setHours(targetHour)
        next.setMinutes(targetMinute)
        next.setSeconds(0)
        next.setMilliseconds(0)

        // If time has passed today, move to tomorrow
        if (next <= now) {
            next.setDate(next.getDate() + 1)
        }
        return next
    }

    // For complex patterns, return approximate time
    next.setHours(parseInt(hour) || 8)
    next.setMinutes(parseInt(minute) || 0)
    next.setSeconds(0)
    next.setMilliseconds(0)

    if (next <= now) {
        next.setDate(next.getDate() + 1)
    }

    return next
}

/**
 * Validate cron expression (basic validation)
 */
export function validateCron(cron: string): boolean {
    if (!cron || cron.trim() === '') {
        return true  // Empty is valid (disabled)
    }

    const parts = cron.trim().split(/\s+/)
    if (parts.length !== 5) {
        return false
    }

    // Basic validation - each part should be valid
    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

    // Check if parts contain valid characters
    const validPattern = /^[\d,\-*/]+$/
    return parts.every(part => validPattern.test(part))
}

/**
 * Format next run time for display
 */
export function formatNextRun(date: Date | null): string {
    if (!date) {
        return 'Not scheduled'
    }

    const now = new Date()
    const diff = date.getTime() - now.getTime()

    if (diff < 0) {
        return 'Calculating...'
    }

    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) {
        return `in ${days} day${days > 1 ? 's' : ''} (${date.toLocaleString()})`
    } else if (hours > 0) {
        return `in ${hours} hour${hours > 1 ? 's' : ''} (${date.toLocaleTimeString()})`
    } else if (minutes > 0) {
        return `in ${minutes} minute${minutes > 1 ? 's' : ''}`
    } else {
        return 'in less than a minute'
    }
}

/**
 * Get day name from day number (0=Sun, 1=Mon, ..., 6=Sat)
 */
export function getDayName(day: number): string {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return days[day] || ''
}
