import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/components/contexts/AuthContext'; // Conceptual path
// import { Home, Users, FileText, Settings, LogOut, BotMessageSquare } from 'lucide-react'; // Conceptual lucide icons

export default function SideNav() {
  const { user, logoutContext } = useAuth();

  const navLinkClasses = "flex items-center px-3 py-2 text-gray-700 hover:bg-gray-200 rounded-md";
  const activeNavLinkClasses = "font-bold bg-gray-200 text-gray-900";

  return (
    <aside className="w-64 h-screen bg-gray-50 border-r border-gray-200 flex flex-col p-4 fixed md:sticky top-0"> {/* Conceptual responsive handling */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-blue-600">Autobidder</h1>
      </div>
      <nav className="flex-grow">
        <ul>
          <li>
            <NavLink 
              to="/dashboard" 
              className={({ isActive }) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}
            >
              {/* <Home size={18} className="mr-2" /> */}
              <span className="mr-2">🏠</span> {/* Placeholder Icon */}
              Dashboard
            </NavLink>
          </li>
          <li className="mt-1">
            <NavLink 
              to="/profiles" 
              className={({ isActive }) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}
            >
              {/* <Users size={18} className="mr-2" /> */}
              <span className="mr-2">👥</span> {/* Placeholder Icon */}
              Profiles
            </NavLink>
          </li>
          <li className="mt-1">
            <NavLink 
              to="/prompts" 
              className={({ isActive }) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}
            >
              {/* <BotMessageSquare size={18} className="mr-2" /> */}
              <span className="mr-2">🤖</span> {/* Placeholder Icon */}
              AI Prompts
            </NavLink>
          </li>
          {user?.account_type === 'agency' && (
            <li className="mt-1">
              <NavLink
                to="/team"
                className={({ isActive }) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}
              >
                <span className="mr-2">👨‍👩‍👧‍👦</span> {/* Placeholder Icon for Team */}
                Team Management
              </NavLink>
            </li>
          )}
          {/* Add other conceptual links as needed */}
          {/* <li><NavLink to="/bids" className={({isActive}) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}>Bids</NavLink></li> */}
          {/* <li><NavLink to="/settings" className={({isActive}) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : ''}`}>Settings</NavLink></li> */}
        </ul>
      </nav>
      <div className="mt-auto pt-4 border-t border-gray-200">
        <div className="mb-2">
          <p className="text-sm font-medium text-gray-700">{user?.name || user?.email || 'User'}</p>
          {user?.role && <p className="text-xs text-gray-500">{user.role}</p>}
        </div>
        {/* <Button onClick={logoutContext} variant="ghost" className="w-full justify-start text-left"> 
            <LogOut size={18} className="mr-2" /> Logout 
        </Button> */}
        <button 
          onClick={logoutContext} 
          className="w-full flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-100 rounded-md"
        >
          {/* <LogOut size={18} className="mr-2" /> */}
          <span className="mr-2">🚪</span> {/* Placeholder Icon */}
          Logout (Conceptual Button)
        </button>
      </div>
    </aside>
  );
}
