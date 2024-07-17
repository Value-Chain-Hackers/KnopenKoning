import React from 'react';
import TabControl from '../components/TabControl';

const AdminPage: React.FC = () => {
  return (
    <div className="admin-page">
      {/* Add your admin page content here */}
      <TabControl url="/admin-tabs.json" />
    </div>
  );
};

export default AdminPage;
