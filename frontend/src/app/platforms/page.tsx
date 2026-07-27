'use client';

import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Navbar } from '@/components/Navbar';
import { apiFetch } from '@/lib/auth';
import { Link2, Check, X, RefreshCw } from 'lucide-react';

const PLATFORMS = [
  { id: 'zomato', name: 'Zomato', color: '#E23744', fields: ['email', 'password'] },
  { id: 'swiggy', name: 'Swiggy', color: '#FC8019', fields: ['phone'] },
  { id: 'blinkit', name: 'Blinkit', color: '#F9CB28', fields: ['email', 'password'] },
  { id: 'instamart', name: 'Instamart', color: '#FC8019', fields: ['phone'] },
];

export default function PlatformsPage() {
  const [connected, setConnected] = useState<Record<string, any>>({});
  const [showForm, setShowForm] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState<string | null>(null);

  useEffect(() => {
    loadCredentials();
  }, []);

  async function loadCredentials() {
    try {
      const res = await apiFetch('/api/credentials');
      const data = await res.json();
      const map: Record<string, any> = {};
      data.forEach((c: any) => { map[c.platform] = c; });
      setConnected(map);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect(platformId: string) {
    setSaving(true);
    try {
      const res = await apiFetch(`/api/credentials?platform=${platformId}`, {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      if (res.ok) {
        setShowForm(null);
        setCredentials({});
        await loadCredentials();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  }

  async function handleSync(platformId: string) {
    setSyncing(platformId);
    try {
      await apiFetch(`/api/sync/${platformId}`, { method: 'POST' });
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(null);
    }
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Connected Platforms</h1>
          <p className="text-gray-500 mb-8">Connect your quick commerce platforms to start tracking commissions.</p>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1,2,3,4].map(i => (
                <div key={i} className="animate-pulse h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {PLATFORMS.map(platform => {
                const isConnected = !!connected[platform.id];
                return (
                  <div key={platform.id} className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center">
                        <div
                          className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                          style={{ backgroundColor: platform.color }}
                        >
                          {platform.name.charAt(0)}
                        </div>
                        <div className="ml-3">
                          <h3 className="font-semibold text-gray-900">{platform.name}</h3>
                          <p className="text-xs text-gray-500">
                            {isConnected ? (
                              <span className="flex items-center text-green-600">
                                <Check className="h-3 w-3 mr-1" /> Connected
                              </span>
                            ) : (
                              <span className="flex items-center text-gray-400">
                                <X className="h-3 w-3 mr-1" /> Not connected
                              </span>
                            )}
                          </p>
                        </div>
                      </div>

                      {isConnected && (
                        <button
                          onClick={() => handleSync(platform.id)}
                          disabled={syncing === platform.id}
                          className="p-2 text-gray-400 hover:text-blue-600 disabled:opacity-50"
                          title="Sync now"
                        >
                          <RefreshCw className={`h-5 w-5 ${syncing === platform.id ? 'animate-spin' : ''}`} />
                        </button>
                      )}
                    </div>

                    {isConnected && connected[platform.id].last_sync_at && (
                      <p className="text-xs text-gray-400 mb-3">
                        Last sync: {new Date(connected[platform.id].last_sync_at).toLocaleString('en-IN')}
                      </p>
                    )}

                    {showForm === platform.id ? (
                      <div className="space-y-3">
                        {platform.fields.map(field => (
                          <input
                            key={field}
                            type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'tel'}
                            placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                            value={credentials[field] || ''}
                            onChange={(e) => setCredentials({ ...credentials, [field]: e.target.value })}
                            className="w-full border border-gray-300 rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-blue-500"
                          />
                        ))}
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleConnect(platform.id)}
                            disabled={saving}
                            className="flex-1 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                          >
                            {saving ? 'Saving...' : 'Connect'}
                          </button>
                          <button
                            onClick={() => { setShowForm(null); setCredentials({}); }}
                            className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setShowForm(platform.id)}
                        className="w-full py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 flex items-center justify-center"
                      >
                        <Link2 className="h-4 w-4 mr-2" />
                        {isConnected ? 'Update Credentials' : 'Connect'}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
