import React, { useEffect, useState } from "react";
import Chart from "./Chart";
import Graph from "./Graph";
import TextContent from "./TextContent";
import DataGrid from "./DataGrid";
import LoadedModels from "./LoadedModels";
import "./TabControl.css";
import FollowUpQuestions from "./FollowUpQuestions";

interface TabControlProps {
  url?: string;
  sessionId?: string;
}

interface Tab {
  id?: string;
  type: string;
  title: string;
  icon?: string 
  content?: string;
  columns?: string[];
  data?: any[];
  dataUrl?: string;
  query?: string;
  sessionId?: string;
  followup?: string[];
}

interface SearchResult {
  title: string;
  body: string;
  url: string;
}

const TabControl: React.FC<TabControlProps> = ({
  url,
  sessionId,
}: TabControlProps) => {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [activeTab, setActiveTab] = useState<number>(0);

  useEffect(() => {
    // Fetch the tabs configuration from the JSON file

    if (sessionId) {
      url = `${url}${sessionId}`;
    }
    fetch(url!)
      .then((response) => response.json())
      .then((data) => {
        console.log("fetch data", data);
        return data;
      })
      .then((data) => {
        setTabs(data.elements);
        setSearchResults(data.search_results);
      });
  }, []);

  const renderTabContent = (tab: Tab, index: number) => {
    let result = null;
    switch (tab.type) {
      case "Graph":
        result = (
          <Graph
            key={`tab-${index}`}
            dataUrl={tab.dataUrl}
            query={tab.query}
          ></Graph>
        );
        break;
      case "Chart":
        result = (
          <Chart key={`tab-${index}`} dataUrl={tab.dataUrl} query={tab.query} />
        );
        break;
      case "Text":
        result = <TextContent key={`tab-${index}`} content={tab.content} />;
        break;
      case "DataGrid":
        result = (
          <DataGrid
            key={`tab-${index}`}
            dataUrl={tab.dataUrl}
            columns={tab.columns}
            query={tab.query}
          />
        );
        break;
      case "LoadedModels":
        result = <LoadedModels key={`tab-${index}`} />;
        break;
      default:
        break;
    }
    return (
      <div>
        {result}
        {tab.followup && <FollowUpQuestions followup={tab.followup} />}
      </div>
    );
  };

  if (!tabs) {
    return <div>Loading...</div>;
  }

  if (tabs.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <div className="tab-control w-full">
        <div className="tab-header flex border-b border-gray-300">
          {tabs.map((tab, index) => (
            <button
              key={index}
              className={`tab-button px-4 py-2 focus:outline-none ${
                index === activeTab ? "active" : ""
              }`}
              onClick={() => setActiveTab(index)}
            >
              <i className={tab.icon}></i> &nbsp;
              {tab.title}
            </button>
          ))}
        </div>
        <div className="tab-panel-content p-4">
          {tabs.length > 0 && renderTabContent(tabs[activeTab], activeTab)}
        </div>
      </div>
      {searchResults.map((result, index) => (
        <div key={index} className="search-result">
          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="search-result-link"
          >
            <h3>{result.title}</h3>
            <p>{result.body}</p>
          </a>
        </div>))
      }
    </>
  );
};

export default TabControl;
