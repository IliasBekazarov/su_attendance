// src/pages/Reports.jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import Button from "../components/Button";

const Reports = () => {
  const data = [
    { name: "Day 1", attendance: 80 },
    { name: "Day 2", attendance: 90 },
    // Add more data from API
  ];

  const handleExport = (format) => {
    console.log(`Exporting to ${format}`);
    // API call for export
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-primary mb-6">Reports</h1>
      <BarChart width={600} height={300} data={data} className="mb-4">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="attendance" fill="#2563eb" animationDuration={1000} />
      </BarChart>
      <div className="space-x-4">
        <Button onClick={() => handleExport("pdf")}>Export PDF</Button>
        <Button onClick={() => handleExport("excel")}>Export Excel</Button>
      </div>
    </div>
  );
};

export default Reports;