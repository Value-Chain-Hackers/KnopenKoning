import React, { useState, useEffect } from "react";
import {
  useTable,
  useSortBy,
  useFilters,
  usePagination,
  Column,
  CellProps,
} from "react-table";
import "./DataGrid.css";

interface DataGridProps {
  id?: string;
  dataUrl?: string;
  data?: any[];
  columns?: any[];
  query?: string;
}

const DataGrid: React.FC<DataGridProps> = ({ data, dataUrl, columns, query }) => {
  const [tableData, setData] = useState<any[]>([]);
  const [tableColumns, setColumns] = useState<Column<any>[]>([]);
  const [queryStr, setQuery] = useState<string>("");
  useEffect(() => {
    setQuery(query || "");
    if (data) {
      setData(data);
    } else if (dataUrl) {
      fetch(dataUrl)
        .then((response) => response.json())
        .then((data) => setData(data));
    } else {
      setData([]);
    }
  }, [data, dataUrl]);

  useEffect(() => {
    if (tableData && tableData.length > 0) {
      const cc = columns!.map((key) => ({
        Header: key,
        accessor: key,
      }));
      setColumns(cc);
    }
  }, [tableData]);

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

  if (!tableData ) {
    return <div>No data</div>;
  }
  return (
    <div>
      <p style={{textAlign:'left'}}>{queryStr}</p>
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
          {rows.map((row, i) => {
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
          })}
        </tbody>
      </table>
    </div>
  );
};

export default DataGrid;
