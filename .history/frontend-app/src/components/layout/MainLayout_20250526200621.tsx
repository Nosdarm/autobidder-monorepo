import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import SideNav from './SideNav';
import TopAppBar from './TopAppBar';

export default function MainLayout() {
  const [isSideNavOpen, setIsSideNavOpen] = useState(false); // For mobile

  const toggleSideNav = () => {
    setIsSideNavOpen(!isSideNavOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* SideNav - conceptual responsive handling */}
      {/* On desktop, always visible */}
      <div className="hidden md:flex md:flex-shrink-0">
        <SideNav />
      </div>
      
      {/* On mobile, conditionally rendered based on isSideNavOpen */}
      {isSideNavOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          {/* Background overlay */}
          <div className="fixed inset-0 bg-black opacity-50" onClick={toggleSideNav}></div>
          <SideNav />
          {/* Optional: Add a close button on the SideNav itself for mobile */}
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopAppBar pageTitle="Current Page Title" onMenuToggle={toggleSideNav} /> {/* pageTitle can be dynamic */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          <Outlet /> {/* Page content will be rendered here */}
        </main>
      </div>
    </div>
  );
}
