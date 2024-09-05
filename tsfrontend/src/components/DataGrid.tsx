import React, { useState, useEffect } from "react";
import {
  useTable,
  useSortBy,
  useFilters,
  usePagination,
  Column,
} from "react-table";
import { useSettings } from "../contexts/SettingsContext";
import "./DataGrid.css";

interface DataGridProps {
  id?: string;
  dataUrl?: string;
  data?: any[];
  columns?: string[];
  query?: string;
}

const DataGrid: React.FC<DataGridProps> = ({ data: initialData, dataUrl, columns, query }) => {
  const settings = useSettings();
  const [tableData, setData] = useState<any[]>([]);
  const [tableColumns, setColumns] = useState<Column<any>[]>([]);
  const [queryStr, setQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery(query || "");
    fetchData();
  }, [query, dataUrl]);

  const fetchData = async () => {
    if (initialData) {
      setData(initialData);
      return;
    }

    setIsLoading(true);
    setError(null);
    if (!query) {
      setIsLoading(false);
      return;
    }
    try {
      const response = await fetch(`${settings.apiUrl}/graph/query`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          url: dataUrl,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result.data || []);
    } catch (e) {
      //setError(`Failed to fetch data: ${e instanceof Error ? e.message : String(e)}`);
      setData([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (columns && columns.length > 0) {
      const cc = columns.map((key) => ({
        Header: key,
        accessor: key,
      }));
      setColumns(cc);
    } else if (tableData && tableData.length > 0) {
      const cc = Object.keys(tableData[0]).map((key) => ({
        Header: key,
        accessor: key,
      }));
      setColumns(cc);
    }
  }, [columns, tableData]);

  const { getTableProps, getTableBodyProps, headerGroups, prepareRow, rows } =
    useTable(
      {
        columns: tableColumns,
        data: tableData,
      },
      useFilters,
      useSortBy,
      usePagination
    );

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      { queryStr && <textarea cols={100} rows={5}  value={queryStr} readOnly={true}></textarea>}
      <table {...getTableProps()}>
        <thead>
          {headerGroups.map((headerGroup) => {
            const { key, ...restHeadGroupProps } = headerGroup.getHeaderGroupProps();
            return (
              <tr key={key} {...restHeadGroupProps}>
                {headerGroup.headers.map((column) => {
                  const { key, ...restHeadProps } = column.getHeaderProps();
                  return (
                    <th key={key} {...restHeadProps}>
                      {column.render("Header")}
                    </th>
                  );
                })}
              </tr>
            );
          })}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.length > 0 ? (
            rows.map((row) => {
              prepareRow(row);
              const { key, ...restRowProps } = row.getRowProps();
              return (
                <tr key={key} {...restRowProps}>
                  {row.cells.map((cell) => {
                    const { key, ...restCellProps } = cell.getCellProps();
                    return (
                      <td key={key} {...restCellProps}>
                        {cell.render("Cell")}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan={tableColumns.length} style={{ textAlign: 'center' }}>
                No data available
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default DataGrid;