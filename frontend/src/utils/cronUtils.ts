/**
 * Convert cron expression to human-readable Chinese text
 */
export function cronToHumanReadable(cron: string): string {
    if (!cron) return '未设置'

    // Interval minutes: */30 * * * *
    const intervalMinutesMatch = cron.match(/^\*\/(\d+) \* \* \* \*$/)
    if (intervalMinutesMatch) {
        const minutes = intervalMinutesMatch[1]
        return `每 ${minutes} 分钟执行一次`
    }

    // Interval hours: 0 */2 * * *
    const intervalHoursMatch = cron.match(/^0 \*\/(\d+) \* \* \*$/)
    if (intervalHoursMatch) {
        const hours = intervalHoursMatch[1]
        return `每 ${hours} 小时执行一次`
    }

    // Daily: 35 6,14,18 * * * (with minute precision)
    const dailyMatch = cron.match(/^(\d+) (\d+(,\d+)*) \* \* \*$/)
    if (dailyMatch) {
        const minute = dailyMatch[1]
        const hours = dailyMatch[2].split(',').map(h => {
            const hour = h.padStart(2, '0')
            const min = minute.padStart(2, '0')
            return `${hour}:${min}`
        })
        return `每天 ${hours.join(', ')} 执行`
    }

    // Weekly: 35 10 * * 1,3,5 (with minute precision)
    const weeklyMatch = cron.match(/^(\d+) (\d+) \* \* (\d+(,\d+)*)$/)
    if (weeklyMatch) {
        const minute = weeklyMatch[1].padStart(2, '0')
        const hour = weeklyMatch[2].padStart(2, '0')
        const dayNumbers = weeklyMatch[3].split(',').map(d => parseInt(d))
        const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
        const days = dayNumbers.map(d => dayNames[d]).join('、')
        return `每${days} ${hour}:${minute} 执行`
    }

    // Custom or unrecognized
    return `自定义: ${cron}`
}
