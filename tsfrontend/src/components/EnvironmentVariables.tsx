import React from 'react';

const EnvironmentVariables: React.FC = () => {
  const envVars = Object.entries(process.env)
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="p-4 bg-gray-100 rounded-lg">
      <h2 className="text-xl font-bold mb-4">Environment Variables</h2>
      {envVars.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {envVars.map(([key, value]) => (
            <div key={key} className="bg-white p-2 rounded shadow">
              <strong className="font-semibold">{key}:</strong> {value}
            </div>
          ))}
        </div>
      ) : (
        <p>No REACT_APP_ environment variables found.</p>
      )}
    </div>
  );
};

export default EnvironmentVariables;