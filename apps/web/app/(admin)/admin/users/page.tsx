"use client";

import { useCallback, useEffect, useState } from "react";
import { RoleChangeModal } from "@/components/admin/RoleChangeModal";
import { apiClient } from "@/lib/api-client";
import { format } from "date-fns";

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  kyc_status: string | null;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
}

interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

type SortField = "email" | "role" | "kyc_status" | "created_at";

interface SortingStateItem {
  id: SortField;
  desc: boolean;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [kycFilter, setKycFilter] = useState("");
  const [sorting, setSorting] = useState<SortingStateItem>({
    id: "created_at",
    desc: true,
  });

  const [roleChangeModal, setRoleChangeModal] = useState<{
    open: boolean;
    user: User | null;
  }>({ open: false, user: null });

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: "20",
        sort_by: sorting.id,
        sort_order: sorting.desc ? "desc" : "asc",
      });

      if (search) params.append("search", search);
      if (roleFilter) params.append("role", roleFilter);
      if (kycFilter) params.append("kyc_status", kycFilter);

      const response = await apiClient.get<UserListResponse>(
        `/admin/users?${params.toString()}`,
      );

      setUsers(response.data.users);
      setTotal(response.data.total);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error("Failed to load users:", error);
    } finally {
      setLoading(false);
    }
  }, [page, search, roleFilter, kycFilter, sorting]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) => (
        <div className="flex flex-col">
          <span className="font-medium">{row.original.email}</span>
          <span className="text-sm text-gray-500">{row.original.name}</span>
        </div>
      ),
    },
    {
      accessorKey: "role",
      header: "Role",
      cell: ({ row }) => {
        const roleColors: Record<string, string> = {
          CUSTOMER: "bg-blue-100 text-blue-800",
          ADMIN: "bg-red-100 text-red-800",
          EXPORTER: "bg-green-100 text-green-800",
          CLEARING_AGENT: "bg-yellow-100 text-yellow-800",
          FINANCE_PARTNER: "bg-purple-100 text-purple-800",
        };

        const role = row.original.role;
        return (
          <span
            className={`px-2 py-1 rounded text-xs font-semibold ${
              roleColors[role] || "bg-gray-100 text-gray-800"
            }`}
          >
            {role}
          </span>
        );
      },
    },
    {
      accessorKey: "kyc_status",
      header: "KYC",
      cell: ({ row }) => {
        const status = row.original.kyc_status;

        if (!status) {
          return <span className="text-gray-400 text-sm">Not Submitted</span>;
        }

        const statusColors: Record<string, string> = {
          PENDING: "bg-yellow-100 text-yellow-800",
          APPROVED: "bg-green-100 text-green-800",
          REJECTED: "bg-red-100 text-red-800",
        };

        return (
          <span
            className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[status]}`}
          >
            {status}
          </span>
        );
      },
    },
    {
      accessorKey: "created_at",
      header: "Joined",
      cell: ({ row }) => (
        <span className="text-sm">
          {format(new Date(row.original.created_at), "MMM d, yyyy")}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex gap-2">
          <button
            onClick={() =>
              setRoleChangeModal({ open: true, user: row.original })
            }
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Change Role
          </button>
          <button
            onClick={() =>
              (window.location.href = `/admin/users/${row.original.id}`)
            }
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
          >
            View
          </button>
        </div>
      ),
    },
  ];

  const table = useReactTable({
    data: users,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
  });

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">User Management</h1>
        <p className="text-gray-600">Manage user accounts and permissions</p>
      </div>

      <div className="mb-6 flex gap-4">
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="flex-1 px-4 py-2 border rounded"
        />

        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="px-4 py-2 border rounded"
        >
          <option value="">All Roles</option>
          <option value="CUSTOMER">Customer</option>
          <option value="ADMIN">Admin</option>
          <option value="EXPORTER">Exporter</option>
          <option value="CLEARING_AGENT">Clearing Agent</option>
          <option value="FINANCE_PARTNER">Finance Partner</option>
        </select>

        <select
          value={kycFilter}
          onChange={(e) => {
            setKycFilter(e.target.value);
            setPage(1);
          }}
          className="px-4 py-2 border rounded"
        >
          <option value="">All KYC Status</option>
          <option value="NONE">Not Submitted</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      <div className="mb-4 text-sm text-gray-600">
        Showing {users.length} of {total} users
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <>
          <div className="border rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort("email")}
                  >
                    <div className="flex items-center gap-2">
                      Email {getSortIndicator("email")}
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort("role")}
                  >
                    <div className="flex items-center gap-2">
                      Role {getSortIndicator("role")}
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort("kyc_status")}
                  >
                    <div className="flex items-center gap-2">
                      KYC {getSortIndicator("kyc_status")}
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort("created_at")}
                  >
                    <div className="flex items-center gap-2">
                      Joined {getSortIndicator("created_at")}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => {
                  const roleColors: Record<string, string> = {
                    CUSTOMER: "bg-blue-100 text-blue-800",
                    ADMIN: "bg-red-100 text-red-800",
                    EXPORTER: "bg-green-100 text-green-800",
                    CLEARING_AGENT: "bg-yellow-100 text-yellow-800",
                    FINANCE_PARTNER: "bg-purple-100 text-purple-800",
                  };

                  const statusColors: Record<string, string> = {
                    PENDING: "bg-yellow-100 text-yellow-800",
                    APPROVED: "bg-green-100 text-green-800",
                    REJECTED: "bg-red-100 text-red-800",
                  };

                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="font-medium">{user.email}</span>
                          <span className="text-sm text-gray-500">
                            {user.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            roleColors[user.role] || "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.kyc_status ? (
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              statusColors[user.kyc_status] ||
                              "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {user.kyc_status}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            Not Submitted
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {format(new Date(user.created_at), "MMM d, yyyy")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-2">
                          <button
                            onClick={() =>
                              setRoleChangeModal({ open: true, user })
                            }
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            Change Role
                          </button>
                          <button
                            onClick={() =>
                              (window.location.href = `/admin/users/${user.id}`)
                            }
                            className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                          >
                            View
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {roleChangeModal.open && roleChangeModal.user && (
        <RoleChangeModal
          user={roleChangeModal.user}
          onClose={() => setRoleChangeModal({ open: false, user: null })}
          onSuccess={() => {
            setRoleChangeModal({ open: false, user: null });
            void loadUsers();
          }}
        />
      )}
    </div>
  );
}
