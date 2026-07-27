'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Navbar } from '@/components/Navbar';
import { apiFetch } from '@/lib/auth';

export default function Dashboard() {
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalOvercharged, setTotalOvercharged] = useState(0);
  const [platformStats, setPlatformStats] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const res = await apiFetch('/api/payments?limit=100');
      const data = await res.json();
      const records = data.data || [];
      setPayments(records);

      // Calculate stats
      let overcharged = 0;
      const stats: Record<string, any> = {};

      records.forEach((r: any) => {
        if (!stats[r.platform]) {
          stats[r.platform] = { orders: 0, sales: 0, commission: 0, overcharged: 0 };
        }
        stats[r.platform].orders++;
        stats[r.platform].sales += r.total_price;
        stats[r.platform].commission += r.actual_commission_charged;
        if (r.commission_difference < 0) {
          stats[r.platform].overcharged += Math.abs(r.commission_difference);
          overcharged += Math.abs(r.commission_difference);
        }
      });

      setTotalOvercharged(overcharged);
      setPlatformStats(stats);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const platformColors: Record<string, string> = {
    zomato: '#E23744',
    swiggy: '#FC8019',
    blinkit: '#F9CB28',
    instamart: '#FC8019',
  };

  const platformBgs: Record<string, string> = {
    zomato: 'bg-red-50 border-red-200',
    swiggy: 'bg-orange-50 border-orange-200',
    blinkit: 'bg-yellow-50 border-yellow-200',
    instamart: 'bg-purple-50 border-purple-200',
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">

          {/* Hero Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-6 text-white shadow-lg shadow-blue-200">
              <p className="text-blue-100 text-sm font-medium">Total Orders</p>
              <p className="text-4xl font-bold mt-1">{payments.length}</p>
              <p className="text-blue-200 text-xs mt-2">Across all platforms</p>
            </div>
            <div className="bg-gradient-to-br from-emerald-600 to-emerald-700 rounded-2xl p-6 text-white shadow-lg shadow-emerald-200">
              <p className="text-emerald-100 text-sm font-medium">Total Sales</p>
              <p className="text-4xl font-bold mt-1">
                ₹{payments.reduce((s, r) => s + r.total_price, 0).toLocaleString('en-IN')}
              </p>
              <p className="text-emerald-200 text-xs mt-2">Gross revenue tracked</p>
            </div>
            <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-2xl p-6 text-white shadow-lg shadow-red-200">
              <p className="text-red-100 text-sm font-medium">Extra Commission Charged</p>
              <p className="text-4xl font-bold mt-1">₹{totalOvercharged.toFixed(2)}</p>
              <p className="text-red-200 text-xs mt-2">Potential savings</p>
            </div>
          </div>

          {/* Platform Cards */}
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Platform Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {Object.entries(platformStats).map(([platform, stats]: [string, any]) => (
              <div
                key={platform}
                className={`rounded-xl border-2 p-5 ${platformBgs[platform] || 'bg-gray-50 border-gray-200'}`}
              >
                <div className="flex items-center mb-3">
                  <div
                    className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                    style={{ backgroundColor: platformColors[platform] || '#6B7280' }}
                  >
                    {platform.charAt(0).toUpperCase()}
                  </div>
                  <h3 className="ml-3 font-semibold text-gray-800 capitalize">{platform}</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Orders</span>
                    <span className="font-medium">{stats.orders}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Sales</span>
                    <span className="font-medium">₹{stats.sales.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Commission</span>
                    <span className="font-medium">₹{stats.commission.toFixed(0)}</span>
                  </div>
                  {stats.overcharged > 0 && (
                    <div className="flex justify-between text-red-600">
                      <span>Overcharged</span>
                      <span className="font-bold">₹{stats.overcharged.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Recent Orders Table */}
          <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h2 className="text-lg font-semibold text-gray-800">Recent Orders</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Platform</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Order ID</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Item</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Amount</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Commission</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Difference</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Net</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {payments.map((r, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white"
                          style={{ backgroundColor: platformColors[r.platform] || '#6B7280' }}
                        >
                          {r.platform}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-gray-600">{r.order_id}</td>
                      <td className="px-6 py-4 text-sm text-gray-800 max-w-[200px] truncate">{r.item_description}</td>
                      <td className="px-6 py-4 text-sm text-right font-medium">₹{r.total_price.toFixed(0)}</td>
                      <td className="px-6 py-4 text-sm text-right text-orange-600">₹{r.actual_commission_charged.toFixed(0)}</td>
                      <td className="px-6 py-4 text-sm text-right">
                        <span className={`font-medium ${r.commission_difference < 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {r.commission_difference < 0 ? '-' : '+'}₹{Math.abs(r.commission_difference).toFixed(2)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-right font-semibold">₹{r.net_settlement.toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
