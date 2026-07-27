'use client';

import { TrendingUp, TrendingDown, DollarSign, AlertTriangle } from 'lucide-react';

interface OverviewData {
  total_overcharged: number;
  by_platform: Record<string, number>;
}

export function OverviewCards({ data }: { data?: OverviewData }) {
  const totalOvercharged = data?.total_overcharged || 0;
  const platformCount = Object.keys(data?.by_platform || {}).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-red-100 text-red-600">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Total Overcharged</p>
            <p className="text-2xl font-semibold text-gray-900">
              ₹{totalOvercharged.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-blue-100 text-blue-600">
            <DollarSign className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Platforms Connected</p>
            <p className="text-2xl font-semibold text-gray-900">{platformCount}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Avg Commission Rate</p>
            <p className="text-2xl font-semibold text-gray-900">18%</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-green-100 text-green-600">
            <TrendingDown className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Potential Savings</p>
            <p className="text-2xl font-semibold text-gray-900">
              ₹{totalOvercharged.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
