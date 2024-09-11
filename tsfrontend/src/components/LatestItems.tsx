import React, { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
const LatestItems = () => {
  const [items, setItems] = useState<any>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const settings = useSettings(); 
  useEffect(() => {
    const fetchLatestItems = async () => {
        await fetch(`${settings.apiUrl}/view/latest`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json',
            }
            }).then(response => response.json())
            .then(data => {
                setItems(data);
                setLoading(false);
            })
            .catch(error => setError(error));
    };
    fetchLatestItems();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-48">Loading...</div>;
  }

  if (error) {
    return (
      <b>Failed to load latest items: {error}</b>
    );
  }

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Your Latest Items</h2>
      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item:any) => (
            <li key={item.id} className="p-3 rounded shadow">
              <h3 className="font-semibold"><a href={'/view/'+ item.id}>{item.question}</a></h3>
            </li>
          ))}
        </ul>
      ) : (
        <p>No items found.</p>
      )}
    </div>
  );
};

export default LatestItems;