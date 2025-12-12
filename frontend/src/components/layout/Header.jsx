import { Bell, User, Search, Settings, ChevronDown, Menu } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/90 border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 max-w-screen-xl mx-auto">
        {/* Left: Logo / Menu / Greeting */}
        <div className="flex items-center gap-4 sm:gap-6 flex-1">
          {/* Mobile Menu */}
          <button className="md:hidden p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition">
            <Menu size={22} strokeWidth={2.5} />
          </button>

          {/* Greeting */}
          <div className="hidden md:flex flex-col">
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">Welcome back, Demo User</h2>
            <p className="text-xs text-gray-500 mt-0.5">Friday, November 14</p>
          </div>

          {/* Desktop Search */}
          <div className="hidden lg:flex items-center gap-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-2xl px-4 py-2 transition-all duration-300 shadow-sm hover:shadow-md min-w-[280px] max-w-[400px] group">
            <Search size={18} className="text-gray-400 group-hover:text-gray-600 transition" strokeWidth={2.5} />
            <input
              type="text"
              placeholder="Search anything..."
              className="bg-transparent border-none outline-none text-sm text-gray-900 placeholder-gray-400 w-full font-medium"
            />
            <kbd className="hidden xl:inline-flex px-2 py-1 text-xs font-semibold text-gray-500 bg-white border border-gray-200 rounded-lg shadow-sm">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Mobile Search */}
          <button className="lg:hidden p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition">
            <Search size={20} strokeWidth={2.5} />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
              }}
              className="relative p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition"
            >
              <Bell size={20} strokeWidth={2.5} />
              <span className="absolute top-1 right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-600 shadow-sm"></span>
              </span>
            </button>

            {showNotifications && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                <div className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="text-gray-900 font-semibold">Notifications</h3>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {[1, 2, 3].map((i) => (
                      <button
                        key={i}
                        className="w-full px-4 py-3 text-left hover:bg-gray-50 transition rounded-lg flex gap-3"
                      >
                        <div className="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center text-white font-bold shadow-sm">
                          {i}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900">Notification {i}</p>
                          <p className="text-xs text-gray-500 line-clamp-2">This is the description of notification {i}.</p>
                          <p className="text-xs text-gray-400 mt-0.5">5 mins ago</p>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="p-3 border-t border-gray-200 bg-gray-50">
                    <button className="w-full py-2 text-sm font-semibold text-blue-600 hover:text-blue-700 rounded-lg hover:bg-blue-50 transition">
                      View all notifications
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Settings */}
          <button className="hidden md:flex p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition">
            <Settings size={20} strokeWidth={2.5} className="hover:rotate-90 transition-transform duration-300" />
          </button>

          {/* Divider */}
          <div className="hidden md:block w-px h-6 bg-gray-200" />

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => {
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 active:bg-gray-200 transition"
            >
              <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center text-gray-700">
                <User size={18} strokeWidth={2.5} />
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-sm font-semibold text-gray-900">Demo User</span>
                <span className="text-xs text-gray-500">Buyer Account</span>
              </div>
              <ChevronDown
                size={16}
                strokeWidth={2.5}
                className={`hidden md:block text-gray-500 transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
              />
            </button>

            {showUserMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                <div className="absolute right-0 mt-3 w-64 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <p className="text-gray-900 font-semibold">Demo User</p>
                    <p className="text-xs text-gray-500">demo@example.com</p>
                  </div>
                  <div className="flex flex-col p-2">
                    {['Profile', 'Settings', 'Billing', 'Help Center'].map((item) => (
                      <button
                        key={item}
                        className="w-full text-left px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 font-medium transition"
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                  <div className="p-2 border-t border-gray-200">
                    <button className="w-full px-4 py-2 text-sm font-bold text-orange-600 hover:bg-orange-50 hover:text-orange-700 rounded-lg transition">
                      Sign Out
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
