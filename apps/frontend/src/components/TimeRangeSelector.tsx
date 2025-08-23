import React from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';

interface TimeRange {
  start: Date;
  end: Date;
  step: string;
}

interface TimeRangeSelectorProps {
  timeRange: TimeRange;
  onTimeRangeChange: (timeRange: TimeRange) => void;
  showStep?: boolean;
}

const QUICK_RANGES = [
  { label: '5m', minutes: 5 },
  { label: '15m', minutes: 15 },
  { label: '30m', minutes: 30 },
  { label: '1h', minutes: 60 },
  { label: '3h', minutes: 180 },
  { label: '6h', minutes: 360 },
  { label: '12h', minutes: 720 },
  { label: '24h', minutes: 1440 },
];

const STEP_OPTIONS = [
  { label: '5s', value: '5s' },
  { label: '15s', value: '15s' },
  { label: '30s', value: '30s' },
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '30m', value: '30m' },
  { label: '1h', value: '1h' },
];

const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  timeRange,
  onTimeRangeChange,
  showStep = true
}) => {
  const handleQuickRange = (minutes: number) => {
    const end = new Date();
    const start = new Date(end.getTime() - minutes * 60 * 1000);
    
    // Auto-select appropriate step based on time range
    let step = timeRange.step;
    if (minutes <= 15) step = '5s';
    else if (minutes <= 60) step = '15s';
    else if (minutes <= 180) step = '30s';
    else if (minutes <= 720) step = '1m';
    else step = '5m';
    
    onTimeRangeChange({ start, end, step });
  };

  const handleStartChange = (value: string) => {
    const start = new Date(value);
    if (!isNaN(start.getTime())) {
      onTimeRangeChange({ ...timeRange, start });
    }
  };

  const handleEndChange = (value: string) => {
    const end = new Date(value);
    if (!isNaN(end.getTime())) {
      onTimeRangeChange({ ...timeRange, end });
    }
  };

  const handleStepChange = (step: string) => {
    onTimeRangeChange({ ...timeRange, step });
  };

  const formatDateTimeLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center">
        <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
        <h3 className="text-sm font-medium text-gray-700">Time Range</h3>
      </div>

      {/* Quick Range Buttons */}
      <div>
        <label className="text-xs font-medium text-gray-600 block mb-2">
          Quick Ranges
        </label>
        <div className="flex flex-wrap gap-2">
          {QUICK_RANGES.map((range) => (
            <button
              key={range.label}
              onClick={() => handleQuickRange(range.minutes)}
              className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Time Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1">
            Start Time
          </label>
          <input
            type="datetime-local"
            value={formatDateTimeLocal(timeRange.start)}
            onChange={(e) => handleStartChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1">
            End Time
          </label>
          <input
            type="datetime-local"
            value={formatDateTimeLocal(timeRange.end)}
            onChange={(e) => handleEndChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      </div>

      {/* Step Selector */}
      {showStep && (
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-2">
            Resolution (Step)
          </label>
          <div className="flex flex-wrap gap-2">
            {STEP_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleStepChange(option.value)}
                className={`px-3 py-1 text-xs font-medium rounded-md border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                  timeRange.step === option.value
                    ? 'bg-blue-100 text-blue-700 border-blue-300'
                    : 'text-gray-700 bg-gray-100 border-gray-300 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Duration Display */}
      <div className="text-xs text-gray-500">
        Duration: {Math.round((timeRange.end.getTime() - timeRange.start.getTime()) / 60000)} minutes
        {showStep && ` • Step: ${timeRange.step}`}
      </div>
    </div>
  );
};

export default TimeRangeSelector;