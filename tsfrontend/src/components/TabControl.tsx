import React, { useEffect, useState } from 'react';
import Chart from './Chart';
import Graph from './Graph';
import TextContent from './TextContent';
import DataGrid from './DataGrid';
import LoadedModels from './LoadedModels';
import "./TabControl.css";

interface TabControlProps {
  url?: string;
  sessionId?: string;
}

interface Tab {
  id?: string;
  type: string;
  title: string;
  content?: string;
  columns?: string[];
  data?: any[];
  dataUrl?: string;
  sessionId?: string;
}

const TabControl: React.FC<TabControlProps> = ({ url }: TabControlProps) => {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeTab, setActiveTab] = useState<number>(0);

  useEffect(() => {
    // Fetch the tabs configuration from the JSON file
    fetch(url!)
      .then(response => response.json())
      .then(data => setTabs(data));
  }, []);

  const renderTabContent = (tab: Tab, index: number) => {
    switch (tab.type) {
      case 'Graph':
        return <Graph key={`tab-${index}`} />;
      case 'Chart':
        return <Chart key={`tab-${index}`} />;
      case 'Text':
        return <TextContent key={`tab-${index}`} content={tab.content} />;
      case 'DataGrid':
        return <DataGrid  key={`tab-${index}`} dataUrl={tab.dataUrl} columns={tab.columns} />;
      case 'LoadedModels':
        return <LoadedModels key={`tab-${index}`} />;
      default:
        return null;
    }
  };

  return (
    <div className="tab-control w-full">
      <div className="tab-header flex border-b border-gray-300">
        {tabs.map((tab, index) => (
          <button
            key={index}
            className={`tab-button px-4 py-2 focus:outline-none ${
              index === activeTab ? 'active' : ''
            }`}
            onClick={() => setActiveTab(index)}
          >
            {tab.title}
          </button>
        ))}
      </div>
      <div className="tab-panel-content p-4">
        {tabs.length > 0 && renderTabContent(tabs[activeTab], activeTab)}
      </div>
    </div>
  );
};

export default TabControl;
