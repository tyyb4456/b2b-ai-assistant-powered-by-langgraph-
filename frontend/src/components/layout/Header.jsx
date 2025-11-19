import { Bell, User, Search, Settings, ChevronDown, Menu } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="sticky top-0 z-50 h-16 bg-linear-to-b from-white via-white to-white/95 backdrop-blur-2xl border-b border-gray-200/80 shadow-lg shadow-gray-200/50">
      <div className="h-full flex items-center justify-between px-4 sm:px-6 max-w-screen-2xl mx-auto">
        {/* Left Section - Logo & Search */}
        <div className="flex items-center gap-3 sm:gap-6 flex-1">
          {/* Mobile Menu */}
          <button className="md:hidden p-2 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 active:scale-95">
            <Menu size={22} strokeWidth={2.5} />
          </button>

          <div className="hidden md:block">
            <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight">
              Welcome back, Demo User
            </h2>
            <p className="text-xs text-gray-500 mt-0.5 font-medium">Friday, November 14</p>
          </div>
          
          {/* Search Bar - Desktop */}
          <div className="hidden lg:flex items-center gap-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-2xl px-4 py-2.5 transition-all duration-300 hover:shadow-lg hover:shadow-gray-200/50 hover:border-gray-300 min-w-[280px] max-w-[400px] group">
            <Search size={18} className="text-gray-400 group-hover:text-gray-600 transition-colors" strokeWidth={2.5} />
            <input 
              type="text" 
              placeholder="Search anything..." 
              className="bg-transparent border-none outline-none text-sm text-gray-900 placeholder:text-gray-400 w-full font-medium"
            />
            <kbd className="hidden xl:inline-flex items-center gap-0.5 px-2.5 py-1 text-xs font-bold text-gray-500 bg-white border border-gray-200 rounded-lg shadow-sm">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Mobile Search */}
          <button className="lg:hidden p-2.5 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 active:scale-95">
            <Search size={20} strokeWidth={2.5} />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button 
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
              }}
              className="relative p-2.5 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 active:scale-95 group"
            >
              <Bell size={20} strokeWidth={2.5} className="group-hover:scale-110 transition-transform" />
              {/* Notification Badge */}
              <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-linear-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/50"></span>
              </span>
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 z-40"
                  onClick={() => setShowNotifications(false)}
                />
                
                <div className="absolute right-0 mt-3 w-[340px] sm:w-[380px] bg-white rounded-3xl shadow-2xl border border-gray-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-4 duration-200">
                  {/* Header */}
                  <div className="p-5 border-b border-gray-200 bg-linear-to-br from-gray-50 to-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-gray-900 text-base">Notifications</h3>
                        <p className="text-xs text-gray-500 mt-1 font-medium">3 unread messages</p>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center">
                        <span className="text-xs font-bold text-red-500">3</span>
                      </div>
                    </div>
                  </div>

                  {/* Notifications List */}
                  <div className="max-h-[400px] overflow-y-auto">
                    {[
                      { title: 'New order received', desc: 'Order #ORD-1001 has been placed', time: '5 mins ago', color: 'from-blue-500 to-cyan-600' },
                      { title: 'Payment confirmed', desc: 'Your payment of $299.99 was successful', time: '10 mins ago', color: 'from-green-500 to-emerald-600' },
                      { title: 'Shipping update', desc: 'Your package will arrive tomorrow', time: '15 mins ago', color: 'from-purple-500 to-pink-600' }
                    ].map((notif, i) => (
                      <button key={i} className="w-full p-4 hover:bg-gray-50 active:bg-gray-100 transition-all duration-200 border-b border-gray-100 last:border-0 text-left group">
                        <div className="flex gap-3">
                          <div className={`w-11 h-11 rounded-2xl bg-linear-to-br ${notif.color} flex items-center justify-center text-white font-bold shadow-lg shrink-0 group-hover:scale-105 transition-transform`}>
                            {i + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 mb-1">{notif.title}</p>
                            <p className="text-xs text-gray-600 line-clamp-2 mb-1.5">{notif.desc}</p>
                            <p className="text-xs text-gray-400 font-medium">{notif.time}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Footer */}
                  <div className="p-3 border-t border-gray-200 bg-gray-50">
                    <button className="w-full py-2.5 text-sm font-bold text-blue-600 hover:text-blue-700 active:text-blue-800 transition-colors rounded-xl hover:bg-blue-50 active:bg-blue-100">
                      View all notifications
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Settings */}
          <button className="hidden md:block p-2.5 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 active:scale-95 group">
            <Settings size={20} strokeWidth={2.5} className="group-hover:rotate-90 transition-transform duration-300" />
          </button>

          {/* Divider */}
          <div className="hidden md:block w-px h-8 bg-gray-200" />

          {/* User Menu */}
          <div className="relative">
            <button 
              onClick={() => {
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className="flex items-center gap-2 sm:gap-3 px-2 sm:px-3 py-2 rounded-xl hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 group"
            >
              <div className="relative">
                <div className="w-9 h-9 bg-linear-to-br from-gray-200 via-gray-300 to-gray-400 rounded-full flex items-center justify-center text-gray-700 font-bold shadow-lg ring-2 ring-gray-200 group-hover:ring-gray-300 transition-all group-hover:scale-105">
                  <User size={18} strokeWidth={2.5} />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-linear-to-br from-green-400 to-green-500 rounded-full border-2 border-white shadow-lg shadow-green-500/50"></div>
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-bold text-gray-900">Demo User</p>
                <p className="text-xs text-gray-500 font-semibold">Buyer Account</p>
              </div>
              <ChevronDown size={16} strokeWidth={2.5} className={`hidden md:block text-gray-500 transition-transform duration-300 ${showUserMenu ? 'rotate-180' : ''}`} />
            </button>

            {/* User Menu Dropdown */}
            {showUserMenu && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 z-40"
                  onClick={() => setShowUserMenu(false)}
                />

                <div className="absolute right-0 mt-3 w-72 bg-white rounded-3xl shadow-2xl border border-gray-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-4 duration-200">
                  {/* User Info */}
                  <div className="p-5 bg-linear-to-br from-gray-50 via-white to-white border-b border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-14 h-14 bg-linear-to-br from-gray-200 via-gray-300 to-gray-400 rounded-2xl flex items-center justify-center text-gray-700 text-lg font-bold shadow-xl ring-2 ring-gray-200">
                          DU
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-linear-to-br from-green-400 to-green-500 rounded-full border-2 border-white shadow-lg"></div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-gray-900 truncate">Demo User</p>
                        <p className="text-xs text-gray-500 truncate font-medium">demo@example.com</p>
                        <div className="mt-1.5 inline-flex items-center gap-1.5 px-2 py-0.5 bg-green-50 rounded-full border border-green-200">
                          <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-xs font-semibold text-green-700">Online</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Menu Items */}
                  <div className="p-2.5">
                    {[
                      { name: 'Profile', icon: '👤' },
                      { name: 'Settings', icon: '⚙️' },
                      { name: 'Billing', icon: '💳' },
                      { name: 'Help Center', icon: '❓' }
                    ].map((item) => (
                      <button key={item.name} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 active:bg-gray-100 transition-all duration-200 font-semibold group">
                        <span className="text-lg group-hover:scale-110 transition-transform"></span>
                        <span>{item.name}</span>
                      </button>
                    ))}
                  </div>

                  {/* Sign Out */}
                  <div className="p-2.5 border-t border-gray-200 bg-gray-50">
                    <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-orange-600 hover:text-orange-700 hover:bg-red-50 active:bg-red-100 transition-all duration-200 font-bold group">
                      <span className="text-lg group-hover:scale-110 transition-transform"></span>
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}