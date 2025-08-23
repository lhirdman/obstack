import React from 'react';
import { Link } from 'react-router-dom';
import { ChartBarIcon, DocumentMagnifyingGlassIcon, CpuChipIcon } from '@heroicons/react/24/outline';

interface User {
  id: number;
  username: string;
  email: string;
  tenant_id: number;
  roles: string[];
}

interface DashboardHomeProps {
  user: User | undefined;
}

const DashboardHome: React.FC<DashboardHomeProps> = ({ user }) => {
  const features = [
    {
      name: 'Metrics',
      description: 'Query and visualize metrics from your observability stack using PromQL',
      href: '/metrics',
      icon: ChartBarIcon,
      available: true,
    },
    {
      name: 'Traces',
      description: 'Explore distributed traces to understand request flows and performance',
      href: '/traces',
      icon: DocumentMagnifyingGlassIcon,
      available: true,
    },
    {
      name: 'Logs',
      description: 'Search and analyze logs from your applications and infrastructure',
      href: '/logs',
      icon: CpuChipIcon,
      available: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Welcome Section */}
          <div className="bg-white shadow rounded-lg mb-8">
            <div className="px-6 py-8">
              <div className="text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  Welcome to ObservaStack, {user?.username}!
                </h2>
                <p className="text-lg text-gray-600 mb-4">
                  Your unified observability platform for metrics, logs, and traces
                </p>
                <div className="flex justify-center space-x-8 text-sm text-gray-500">
                  <div>
                    <span className="font-medium">Tenant:</span> {user?.tenant_id}
                  </div>
                  <div>
                    <span className="font-medium">Roles:</span> {user?.roles?.join(', ') || 'None'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.name}
                className={`relative bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow ${
                  !feature.available ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <feature.icon
                      className={`h-8 w-8 ${
                        feature.available ? 'text-blue-600' : 'text-gray-400'
                      }`}
                      aria-hidden="true"
                    />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {feature.name}
                      {!feature.available && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Coming Soon
                        </span>
                      )}
                    </h3>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-gray-500">{feature.description}</p>
                </div>
                {feature.available && (
                  <div className="mt-6">
                    <Link
                      to={feature.href}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Open {feature.name}
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Quick Stats */}
          <div className="mt-8 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Quick Stats</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">2</div>
                  <div className="text-sm text-gray-500">Available Features</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">Active</div>
                  <div className="text-sm text-gray-500">System Status</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{user?.tenant_id}</div>
                  <div className="text-sm text-gray-500">Tenant ID</div>
                </div>
              </div>
            </div>
          </div>

          {/* Getting Started */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="p-6">
              <h3 className="text-lg font-medium text-blue-900 mb-4">Getting Started</h3>
              <div className="space-y-3 text-sm text-blue-800">
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-xs font-medium text-blue-900 mr-3 mt-0.5">
                    1
                  </div>
                  <div>
                    <strong>Explore Metrics:</strong> Click on the Metrics feature to start querying your observability data using PromQL.
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-xs font-medium text-blue-900 mr-3 mt-0.5">
                    2
                  </div>
                  <div>
                    <strong>Try Sample Queries:</strong> Use the built-in query examples to get familiar with common monitoring patterns.
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-xs font-medium text-blue-900 mr-3 mt-0.5">
                    3
                  </div>
                  <div>
                    <strong>Customize Time Ranges:</strong> Use the time range selector to focus on specific time periods for your analysis.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardHome;