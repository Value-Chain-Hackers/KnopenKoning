import React from 'react';
interface ChartProps {
  id?: string;
  dataUrl?: string;
  data?: any[];
  query?: string;
}

const Chart: React.FC<ChartProps> = ({ data: initialData, dataUrl, query }) => {
  return (
    <div>
      <h2>Chart Content</h2>
      { query && <textarea cols={100} rows={5}  value={query} readOnly={true}></textarea>}
      {/* Add chart rendering logic here */}
    </div>
  );
};

export default Chart;
