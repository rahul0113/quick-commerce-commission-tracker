'use client';

import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface Alert {
  platform: string;
  order_id: string;
  expected: number;
  actual: number;
  difference: number;
  severity: 'low' | 'medium' | 'high';
  message: string;
}

const severityConfig = {
  high: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  medium: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  low: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
};

export function AlertsList({ alerts }: { alerts?: Alert[] }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Commission Alerts</h3>
        <p className="text-gray-500">No alerts - all commissions look correct!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Commission Alerts ({alerts.length})
      </h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.slice(0, 10).map((alert, index) => {
          const config = severityConfig[alert.severity];
          const Icon = config.icon;

          return (
            <div
              key={index}
              className={`p-4 rounded-lg border ${config.bg} ${config.border}`}
            >
              <div className="flex items-start">
                <Icon className={`h-5 w-5 ${config.color} mt-0.5`} />
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">
                      {alert.platform.charAt(0).toUpperCase() + alert.platform.slice(1)}
                    </span>
                    <span className={`text-sm font-semibold ${
                      alert.difference < 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {alert.difference < 0 ? '-' : '+'}₹{Math.abs(alert.difference).toFixed(2)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-1">Order: {alert.order_id}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
