'use client';

import { useState, useEffect } from 'react';
import { OverviewCards } from '@/components/OverviewCards';
import { PlatformChart } from '@/components/PlatformChart';
import { CommissionTable } from '@/components/CommissionTable';
import { AlertsList } from '@/components/AlertsList';

function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
}

async function apiFetch(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    // Token expired or invalid — redirect to login
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  return res;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      if ((err as Error).message !== 'Unauthorized') {
        console.error('Failed to fetch data:', err);
        setError('Failed to load data');
      }
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

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error}</p>
          <button onClick={() => fetchData()} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
            Retry
          </button>
        </div>
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
