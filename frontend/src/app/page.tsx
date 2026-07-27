'use client';

import { useState, useEffect } from 'react';
import { OverviewCards } from '@/components/OverviewCards';
import { PlatformChart } from '@/components/PlatformChart';
import { CommissionTable } from '@/components/CommissionTable';
import { AlertsList } from '@/components/AlertsList';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString(),
    endDate: new Date().toISOString(),
  });

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  async function fetchData() {
    try {
      const [summaryRes, overchargedRes, alertsRes] = await Promise.all([
        fetch(`/api/summary?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
        fetch(`/api/overcharged?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
        fetch(`/api/alerts?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
      ]);

      const [summary, overcharged, alerts] = await Promise.all([
        summaryRes.json(),
        overchargedRes.json(),
        alertsRes.json(),
      ]);

      setData({ summary, overcharged, alerts });
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">Commission Tracker</h1>
          <p className="text-sm text-gray-500">Track commissions across quick commerce platforms</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <OverviewCards data={data?.overcharged} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <PlatformChart data={data?.summary} />
          <AlertsList alerts={data?.alerts?.alerts} />
        </div>

        <div className="mt-8">
          <CommissionTable data={data?.summary} />
        </div>
      </main>
    </div>
  );
}
