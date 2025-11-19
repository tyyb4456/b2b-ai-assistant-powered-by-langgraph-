import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <Sidebar />
      
      <div className="ml-64">
        <Header />
        
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
}