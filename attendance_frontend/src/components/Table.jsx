import React from 'react';

const Table = ({ columns, data }) => {
  return (
    <table className="min-w-full bg-white border">
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.accessor} className="py-2 px-4 border">
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, index) => (
          <tr key={index}>
            {columns.map((column) => (
              <td key={column.accessor} className="py-2 px-4 border">
                {column.render ? column.render(row[column.accessor]) : row[column.accessor]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Table;