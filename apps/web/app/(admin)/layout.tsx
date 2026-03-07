import { ReactNode } from "react";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <nav className="p-4">
          <h2 className="text-xl font-bold mb-4">Admin Panel</h2>
          <ul className="space-y-2">
            <li>
              <a
                href="/admin/dashboard"
                className="block p-2 hover:bg-gray-800 rounded"
              >
                Dashboard
              </a>
            </li>
            <li>
              <a
                href="/admin/users"
                className="block p-2 hover:bg-gray-800 rounded"
              >
                User Management
              </a>
            </li>
            <li>
              <a
                href="/admin/orders"
                className="block p-2 hover:bg-gray-800 rounded"
              >
                Orders
              </a>
            </li>
            <li>
              <a
                href="/admin/kyc"
                className="block p-2 hover:bg-gray-800 rounded"
              >
                KYC Review
              </a>
            </li>
            <li>
              <a
                href="/admin/audit-logs"
                className="block p-2 hover:bg-gray-800 rounded"
              >
                Audit Logs
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
