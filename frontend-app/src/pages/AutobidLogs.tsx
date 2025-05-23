import AIScoreChart from './AIScoreChart';
import React, { useEffect, useState } from 'react';
import api from '../../lib/axios'; // Updated axios import
import { useParams } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';


type Log = {
  id: number;
  job_title: string;
  job_link: string;
  bid_text?: string | null; // Align with backend Optional[str]
  status: string;
  created_at: string; // Or Date if parsed, but string is fine from JSON
  // profile_id, error_message etc. from AutobidLogOut can be added if needed by UI
};

const AutobidLogs: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>(); // Typed profileId
  const [logs, setLogs] = useState<Log[]>([]);
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'error'>('all');
  const [daysFilter, setDaysFilter] = useState<number>(7);
  const [chartData, setChartData] = useState<{ date: string; count: number }[]>([]);
  const [error, setError] = useState<string | null>(null); // Added error state

  useEffect(() => {
    if (!profileId) return;
    setError(null); // Clear previous errors

    api.get<Log[]>(`/autobidder/logs/${profileId}`) // Use api instance, updated path, generic type
      .then(res => {
        let filtered = res.data; // Type is already Log[] due to generic

        if (statusFilter !== 'all') {
        filtered = filtered.filter(log => log.status === statusFilter);
      }

      if (daysFilter > 0) {
        const since = new Date();
        since.setDate(since.getDate() - daysFilter);
        filtered = filtered.filter(log => new Date(log.created_at) >= since);
      }

      setLogs(filtered);

      // 📊 Группировка по дням
      const grouped: Record<string, number> = {};
      for (let i = 0; i < daysFilter; i++) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const key = date.toISOString().split('T')[0];
        grouped[key] = 0;
      }

      for (const log of filtered) {
        const key = log.created_at.split('T')[0];
        if (grouped[key] !== undefined) {
          grouped[key]++;
        }
      }

      const chart = Object.entries(grouped)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, count]) => ({ date, count }));

      setChartData(chart);
    })
    .catch(err => {
      console.error("Ошибка загрузки логов:", err);
      setError("Не удалось загрузить логи. Пожалуйста, попробуйте позже.");
    });
  }, [profileId, statusFilter, daysFilter]);

  return (
    <div className="p-4 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Логи авто-биддера для профиля #{profileId}</h2>
      
      {error && <div className="text-red-500 mb-4 p-2 border border-red-300 rounded">{error}</div>}

      <div className="flex gap-4 mb-6 items-center">
        <label>
          Статус:{' '}
          <select
            className="border px-2 py-1 rounded"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as any)}
          >
            <option value="all">Все</option>
            <option value="success">Успешные</option>
            <option value="error">Ошибки</option>
          </select>
        </label>
        <label>
          За сколько дней:{' '}
          <select
            className="border px-2 py-1 rounded"
            value={daysFilter}
            onChange={e => setDaysFilter(parseInt(e.target.value))}
          >
            <option value={1}>1 день</option>
            <option value={3}>3 дня</option>
            <option value={7}>7 дней</option>
            <option value={0}>Всё время</option>
          </select>
        </label>
      </div>
      <AIScoreChart logs={logs} />


      {chartData.length > 0 && daysFilter > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-2">Отклики по дням</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <table className="w-full text-sm border">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 border">Дата</th>
            <th className="p-2 border">Джоба</th>
            <th className="p-2 border">Статус</th>
            <th className="p-2 border">Отклик</th>
          </tr>
        </thead>
        <tbody>
        {logs.map(log => (
        <tr
                 key={log.id}
                className={`hover:bg-gray-50 ${log.status === 'success' ? 'bg-green-50' : ''}`}
  >
    <td className="p-2 border whitespace-nowrap">
      {new Date(log.created_at).toLocaleString()}
    </td>
    <td className="p-2 border">
      <a
        href={log.job_link}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:underline"
      >
        {log.job_title}
      </a>
    </td>
    <td className={`p-2 border font-semibold ${log.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
      {log.status}
    </td>
    <td className="p-2 border max-w-xs truncate" title={log.bid_text}>
      {log.bid_text}
    </td>
  </tr>
))}

        </tbody>
      </table>

      {logs.length === 0 && (
        <p className="text-center text-gray-500 mt-4">Нет логов по заданным фильтрам.</p>
      )}
    </div>
  );
};

export default AutobidLogs;
