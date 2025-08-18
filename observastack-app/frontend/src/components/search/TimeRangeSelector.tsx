import React, { useState } from 'react'
import { Popover, Transition } from '@headlessui/react'
import { ClockIcon, CalendarIcon } from '@heroicons/react/24/outline'
import { Button, Input } from '../ui'
import { TimeRange } from '../../types'
import { format, parseISO, isValid } from 'date-fns'
import { clsx } from 'clsx'

export interface TimeRangeSelectorProps {
  value: TimeRange
  onChange: (timeRange: TimeRange) => void
  className?: string
}

const quickRanges = [
  { label: 'Last 15 minutes', value: { from: 'now-15m', to: 'now' } },
  { label: 'Last 30 minutes', value: { from: 'now-30m', to: 'now' } },
  { label: 'Last 1 hour', value: { from: 'now-1h', to: 'now' } },
  { label: 'Last 3 hours', value: { from: 'now-3h', to: 'now' } },
  { label: 'Last 6 hours', value: { from: 'now-6h', to: 'now' } },
  { label: 'Last 12 hours', value: { from: 'now-12h', to: 'now' } },
  { label: 'Last 24 hours', value: { from: 'now-24h', to: 'now' } },
  { label: 'Last 7 days', value: { from: 'now-7d', to: 'now' } },
  { label: 'Last 30 days', value: { from: 'now-30d', to: 'now' } }
]

function formatTimeRange(timeRange: TimeRange): string {
  // Check if it's a quick range
  const quickRange = quickRanges.find(
    range => range.value.from === timeRange.from && range.value.to === timeRange.to
  )
  
  if (quickRange) {
    return quickRange.label
  }

  // Try to format as dates
  try {
    if (timeRange.from.startsWith('now')) {
      return `${timeRange.from} to ${timeRange.to}`
    }
    
    const fromDate = parseISO(timeRange.from)
    const toDate = parseISO(timeRange.to)
    
    if (isValid(fromDate) && isValid(toDate)) {
      return `${format(fromDate, 'MMM d, HH:mm')} - ${format(toDate, 'MMM d, HH:mm')}`
    }
  } catch {
    // Fall back to raw values
  }
  
  return `${timeRange.from} to ${timeRange.to}`
}

export function TimeRangeSelector({
  value,
  onChange,
  className
}: TimeRangeSelectorProps) {
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [mode, setMode] = useState<'quick' | 'custom'>('quick')

  const handleQuickRangeSelect = (range: TimeRange) => {
    onChange(range)
  }

  const handleCustomRangeApply = () => {
    if (customFrom && customTo) {
      onChange({
        from: customFrom,
        to: customTo
      })
    }
  }

  const formatDateTimeLocal = (isoString: string): string => {
    try {
      const date = parseISO(isoString)
      if (isValid(date)) {
        return format(date, "yyyy-MM-dd'T'HH:mm")
      }
    } catch {
      // Ignore parsing errors
    }
    return ''
  }

  return (
    <Popover className={clsx('relative', className)}>
      <Popover.Button as={Button} variant="outline" className="gap-2">
        <ClockIcon className="h-4 w-4" />
        {formatTimeRange(value)}
      </Popover.Button>

      <Transition
        as={React.Fragment}
        enter="transition ease-out duration-200"
        enterFrom="opacity-0 translate-y-1"
        enterTo="opacity-100 translate-y-0"
        leave="transition ease-in duration-150"
        leaveFrom="opacity-100 translate-y-0"
        leaveTo="opacity-0 translate-y-1"
      >
        <Popover.Panel className="absolute z-10 mt-2 w-80 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="p-4">
            {/* Mode selector */}
            <div className="flex border-b border-gray-200 mb-4">
              <button
                type="button"
                onClick={() => setMode('quick')}
                className={clsx(
                  'flex-1 py-2 px-3 text-sm font-medium border-b-2 transition-colors',
                  mode === 'quick'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                Quick ranges
              </button>
              <button
                type="button"
                onClick={() => setMode('custom')}
                className={clsx(
                  'flex-1 py-2 px-3 text-sm font-medium border-b-2 transition-colors',
                  mode === 'custom'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                Custom range
              </button>
            </div>

            {mode === 'quick' ? (
              <div className="space-y-1">
                {quickRanges.map((range, index) => (
                  <Popover.Button
                    key={index}
                    as="button"
                    type="button"
                    onClick={() => handleQuickRangeSelect(range.value)}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-sm rounded-md transition-colors',
                      value.from === range.value.from && value.to === range.value.to
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                  >
                    {range.label}
                  </Popover.Button>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    From
                  </label>
                  <Input
                    type="datetime-local"
                    value={customFrom || formatDateTimeLocal(value.from)}
                    onChange={(e) => setCustomFrom(e.target.value)}
                    leftIcon={<CalendarIcon />}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    To
                  </label>
                  <Input
                    type="datetime-local"
                    value={customTo || formatDateTimeLocal(value.to)}
                    onChange={(e) => setCustomTo(e.target.value)}
                    leftIcon={<CalendarIcon />}
                  />
                </div>
                <Popover.Button
                  as={Button}
                  onClick={handleCustomRangeApply}
                  disabled={!customFrom || !customTo}
                  className="w-full"
                >
                  Apply Custom Range
                </Popover.Button>
              </div>
            )}
          </div>
        </Popover.Panel>
      </Transition>
    </Popover>
  )
}