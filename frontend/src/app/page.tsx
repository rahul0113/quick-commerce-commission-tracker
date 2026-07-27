'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Navbar } from '@/components/Navbar';
import { OverviewCards } from '@/components/OverviewCards';
import { PlatformChart } from '@/components/PlatformChart';
import { CommissionTable } from '@/components/CommissionTable';
import { AlertsList } from '@/components/AlertsList';
import { apiFetch } from '@/lib/auth';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange] = useState({
    startDate: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString(),
    endDate: new Date().toISOString(),
  });

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [summaryRes, overchargedRes, alertsRes] = await Promise.all([
        apiFetch(`/api/summary?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
        apiFetch(`/api/overcharged?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
        apiFetch(`/api/alerts?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`),
      ]);

      const [summary, overcharged, alerts] = await Promise.all([
        summaryRes.json(),
        overchargedRes.json(),
        alertsRes.json(),
      ]);

      setData({ summary, overcharged, alerts });
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[1,2,3,4].map(i => (
                <div key={i} className="animate-pulse h-24 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          ) : (
            <>
              <OverviewCards data={data?.overcharged} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
                <PlatformChart data={data?.summary} />
                <AlertsList alerts={data?.alerts?.alerts} />
              </div>
              <div className="mt-8">
                <CommissionTable data={data?.summary} />
              </div>
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
