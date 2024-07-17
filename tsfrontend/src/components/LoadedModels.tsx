import React, {useContext, useState, useEffect} from 'react';

const toHumanReadable = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const Chart: React.FC = () => {
    const [data, setData] = useState<any[]>([]);
    useEffect(() => {
        fetch('http://localhost:18000/ai/models/loaded')
            .then((response) => response.json())
            .then((data) => setData(data));
    }, []);
    if (!data) {
        return <div>No data</div>;
    }
  return (
    <div>
      <h2>Loaded Models</h2>
      {data.map((model, index) => (
        <>
           <div>{model.name}</div>
           {/* Display gpu formated as % */}
          <div>{model.gpu*100}%</div>
          <div>{toHumanReadable(model.size)}</div>
        </> 
      ))}
    </div>
  );
};

export default Chart;
