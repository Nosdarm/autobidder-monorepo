import React, { useState, useRef } from 'react'; // Added useRef
import { Outlet } from 'react-router-dom';
import SideNav from './SideNav';
import TopAppBar from './TopAppBar';

export default function MainLayout() {
  const [isSideNavOpen, setIsSideNavOpen] = useState(false); // For mobile

  const toggleSideNav = () => {
    setIsSideNavOpen(!isSideNavOpen);
  };

  return (
    <div className="flex h-screen bg-background text-foreground"> {/* Updated bg-gray-100 to bg-background */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:p-3 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>
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
        <main id="main-content" tabIndex={-1} className="flex-1 overflow-x-hidden overflow-y-auto bg-background p-6 focus:outline-none"> {/* Added id, tabIndex, focus:outline-none and updated bg */}
          <Outlet /> {/* Page content will be rendered here */}
        </main>
      </div>
    </div>
  );
}
