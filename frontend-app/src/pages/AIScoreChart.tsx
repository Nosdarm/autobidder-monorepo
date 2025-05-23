import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

type Log = {
  id: number;
  score?: number;
};

type Props = {
  logs: Log[];
};

const AIScoreChart: React.FC<Props> = ({ logs }) => {
  const grouped: Record<number, number> = {};

  for (let score = 0; score <= 10; score++) {
    grouped[score] = 0;
  }

  for (const log of logs) {
    if (typeof log.score === 'number') {
      const bucket = Math.round(log.score);
      if (bucket >= 0 && bucket <= 10) {
        grouped[bucket]++;
      }
    }
  }

  const chartData = Object.entries(grouped).map(([score, count]) => ({
    score,
    count,
  }));

  if (chartData.every(item => item.count === 0)) {
    return null;
  }

  return (
    <div className="mb-8">
      <h3 className="text-lg font-semibold mb-2">AI Score (релевантность)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="score" label={{ value: "Score", position: "insideBottom", offset: -5 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AIScoreChart;