import React, { useMemo } from 'react';
// @ts-ignore - echarts-for-react doesn't have proper types
import ReactECharts from 'echarts-for-react';
import { format } from 'date-fns';

interface MetricsResponse {
  status: string;
  data: {
    resultType: string;
    result: any[];
  };
}

interface MetricsChartProps {
  data: MetricsResponse;
  queryType: 'instant' | 'range';
  query: string;
}

const MetricsChart: React.FC<MetricsChartProps> = ({ data, queryType, query }) => {
  const formatMetricName = (metric: Record<string, string>): string => {
    if (!metric) return 'Unknown';
    
    // Extract the metric name
    const metricName = metric.__name__ || 'metric';
    
    // Get other labels (excluding __name__)
    const labels = Object.entries(metric)
      .filter(([key]) => key !== '__name__')
      .map(([key, value]) => `${key}="${value}"`)
      .join(', ');
    
    return labels ? `${metricName}{${labels}}` : metricName;
  };

  const getColor = (index: number): string => {
    const colors = [
      '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
      '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ];
    return colors[index % colors.length] || '#3b82f6';
  };

  const chartOptions = useMemo(() => {
    if (!data?.data?.result || data.data.result.length === 0) {
      return null;
    }

    const result = data.data.result;

    if (queryType === 'instant') {
      // For instant queries, create a bar chart or table
      const series = result.map((item, index) => ({
        name: formatMetricName(item.metric),
        value: parseFloat(item.value[1]),
        itemStyle: {
          color: getColor(index)
        }
      }));

      return {
        title: {
          text: `Instant Query: ${query}`,
          left: 'center',
          textStyle: {
            fontSize: 14,
            fontWeight: 'normal'
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: (params: any) => {
            return `${params.name}<br/>Value: ${params.value}`;
          }
        },
        xAxis: {
          type: 'category',
          data: series.map(s => s.name),
          axisLabel: {
            rotate: 45,
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          type: 'bar',
          data: series,
          itemStyle: {
            borderRadius: [4, 4, 0, 0]
          }
        }],
        grid: {
          left: '10%',
          right: '10%',
          bottom: '20%',
          top: '15%'
        }
      };
    } else {
      // For range queries, create a time series line chart
      const series = result.map((item, index) => {
        const values = item.values || [];
        const data = values.map((value: [number, string]) => [
          value[0] * 1000, // Convert to milliseconds
          parseFloat(value[1])
        ]);

        return {
          name: formatMetricName(item.metric),
          type: 'line',
          data: data,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: getColor(index)
          },
          areaStyle: data.length === 1 ? undefined : {
            opacity: 0.1,
            color: getColor(index)
          }
        };
      });

      return {
        title: {
          text: `Range Query: ${query}`,
          left: 'center',
          textStyle: {
            fontSize: 14,
            fontWeight: 'normal'
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: (params: any) => {
            if (!params || params.length === 0) return '';
            
            const time = format(new Date(params[0].value[0]), 'yyyy-MM-dd HH:mm:ss');
            let content = `${time}<br/>`;
            
            params.forEach((param: any) => {
              content += `${param.seriesName}: ${param.value[1]}<br/>`;
            });
            
            return content;
          }
        },
        legend: {
          type: 'scroll',
          bottom: 0,
          textStyle: {
            fontSize: 10
          }
        },
        xAxis: {
          type: 'time',
          axisLabel: {
            formatter: (value: number) => format(new Date(value), 'HH:mm:ss'),
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 10
          }
        },
        series: series,
        grid: {
          left: '10%',
          right: '10%',
          bottom: series.length > 1 ? '15%' : '10%',
          top: '15%'
        },
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0
          },
          {
            type: 'slider',
            xAxisIndex: 0,
            height: 20,
            bottom: series.length > 1 ? '5%' : '0%'
          }
        ]
      };
    }
  }, [data, queryType, query]);


  if (!data?.data?.result || data.data.result.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No data</h3>
          <p className="mt-1 text-sm text-gray-500">
            The query returned no results. Try adjusting your query or time range.
          </p>
        </div>
      </div>
    );
  }

  if (!chartOptions) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500">
          <h3 className="text-sm font-medium">Unable to render chart</h3>
          <p className="mt-1 text-sm">The data format is not supported for visualization.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <ReactECharts
        option={chartOptions}
        style={{ height: '400px', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
      
      {/* Data Summary */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Query Results Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Result Type:</span>
            <span className="ml-2 font-medium">{data.data.resultType}</span>
          </div>
          <div>
            <span className="text-gray-500">Series Count:</span>
            <span className="ml-2 font-medium">{data.data.result.length}</span>
          </div>
          {queryType === 'range' && data.data.result.length > 0 && (
            <div>
              <span className="text-gray-500">Data Points:</span>
              <span className="ml-2 font-medium">
                {data.data.result.reduce((sum, item) => sum + (item.values?.length || 0), 0)}
              </span>
            </div>
          )}
          <div>
            <span className="text-gray-500">Status:</span>
            <span className="ml-2 font-medium text-green-600">{data.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsChart;