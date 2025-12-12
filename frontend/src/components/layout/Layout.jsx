// src/Layout.jsx
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import Breadcrumbs from './Breadcrumbs';

export default function Layout() {
  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="ml-64">
        {/* Header */}
        <Header />
        
        {/* Page Content (rendered by child routes) */}
        <main className="min-h-[calc(100vh-4rem)]">
          <div className="max-w-xxl mx-auto px-6 py-6">
            <Breadcrumbs />
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}