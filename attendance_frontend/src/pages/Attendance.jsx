import { useState, useEffect, useContext } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import Table from '../components/Table';
import Spinner from '../components/Spinner';

const Attendance = () => {
  const { user } = useContext(AuthContext);
  const [attendances, setAttendances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    student: '',
    schedule: '',
    is_present: false,
  });

  useEffect(() => {
    const fetchAttendances = async () => {
      try {
        const response = await api.get('/attendance/');
        setAttendances(response.data);
      } catch (error) {
        toast.error('Failed to load attendance records');
      } finally {
        setLoading(false);
      }
    };
    fetchAttendances();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/attendance/', {
        ...formData,
        is_present: formData.is_present === 'true',
      });
      toast.success('Attendance added successfully');
      const response = await api.get('/attendance/');
      setAttendances(response.data);
      setFormData({ student: '', schedule: '', is_present: false });
    } catch (error) {
      toast.error('Failed to add attendance');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Student ID', accessor: 'student' },
    { header: 'Schedule ID', accessor: 'schedule' },
    { header: 'Present', accessor: 'is_present', render: (value) => (value ? 'Yes' : 'No') },
    { header: 'Date', accessor: 'date' },
  ];

  if (loading) {
    return <Spinner />;
  }

  return (
    <div className="container mx-auto">
      <h1 className="text-2xl font-bold mb-6">Катышуу</h1>
      {user.role === 'teacher' && (
        <div className="mb-6 bg-white p-6 rounded shadow-md">
          <h2 className="text-xl font-semibold mb-4">Жаңы катышуу кошуу</h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700">Студент ID</label>
                <input
                  type="text"
                  name="student"
                  value={formData.student}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-700">Расписание ID</label>
                <input
                  type="text"
                  name="schedule"
                  value={formData.schedule}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-gray-700">Келдиби?</label>
                <select
                  name="is_present"
                  value={formData.is_present}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                >
                  <option value="true">Ооба</option>
                  <option value="false">Жок</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="mt-4 bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
            >
              Кошуу
            </button>
          </form>
        </div>
      )}
      <Table columns={columns} data={attendances} />
    </div>
  );
};

export default Attendance;