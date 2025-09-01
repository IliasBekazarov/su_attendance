import { useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const Sidebar = () => {
  const { user } = useContext(AuthContext);

  const menuItems = {
    admin: [
      { path: '/dashboard', label: 'Дашборд' },
      { path: '/users', label: 'Колдонуучулар' },
      { path: '/groups', label: 'Группалар' },
      { path: '/reports', label: 'Отчеттор' },
    ],
    teacher: [
      { path: '/dashboard', label: 'Дашборд' },
      { path: '/schedule', label: 'Расписание' },
      { path: '/attendance', label: 'Катышуу' },
    ],
    student: [
      { path: '/dashboard', label: 'Дашборд' },
      { path: '/schedule', label: 'Расписание' },
      { path: '/student-profile', label: 'Профиль' },
    ],
  };

  return (
    <div className="fixed top-0 left-0 h-full w-64 bg-gray-800 text-white p-4">
      <h2 className="text-xl font-bold mb-6">Меню</h2>
      <ul>
        {user &&
          menuItems[user.role]?.map((item) => (
            <li key={item.path} className="mb-2">
              <Link to={item.path} className="hover:bg-gray-700 p-2 rounded block">
                {item.label}
              </Link>
            </li>
          ))}
      </ul>
    </div>
  );
};

export default Sidebar;