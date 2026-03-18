"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { RoleChangeModal } from "@/components/admin/RoleChangeModal";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from "@tanstack/react-table";
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

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [kycFilter, setKycFilter] = useState("");

  // Sorting
  const [sorting, setSorting] = useState<SortingState>([
    { id: "created_at", desc: true },
  ]);

  // Role change modal
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
      });

      if (search) params.append("search", search);
      if (roleFilter) params.append("role", roleFilter);
      if (kycFilter) params.append("kyc_status", kycFilter);

      if (sorting.length > 0) {
        params.append("sort_by", sorting[0].id);
        params.append("sort_order", sorting[0].desc ? "desc" : "asc");
      }

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
          <span className="text-sm text-[#546a7b]">{row.original.name}</span>
        </div>
      ),
    },
    {
      accessorKey: "role",
      header: "Role",
      cell: ({ row }) => {
        const roleColors: Record<string, string> = {
          CUSTOMER: "bg-blue-500/10 text-blue-200 border border-blue-500/20",
          ADMIN: "bg-red-500/10 text-red-200 border border-red-500/20",
          EXPORTER:
            "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
          CLEARING_AGENT:
            "bg-amber-500/10 text-amber-200 border border-amber-500/20",
          FINANCE_PARTNER:
            "bg-purple-500/10 text-purple-200 border border-purple-500/20",
        };

        const role = row.original.role;
        return (
          <span
            className={`px-2 py-1 rounded text-xs font-semibold ${
              roleColors[role] ||
              "bg-[#c6c5b9]/30 text-gray-200 border border-[#c6c5b9]/50"
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
          return <span className="text-[#546a7b] text-sm">Not Submitted</span>;
        }

        const statusColors: Record<string, string> = {
          PENDING: "bg-amber-500/10 text-amber-200 border border-amber-500/20",
          APPROVED:
            "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
          REJECTED: "bg-red-500/10 text-red-200 border border-red-500/20",
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
            className="px-3 py-1 rounded text-sm bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
          >
            Change Role
          </button>
          <button
            onClick={() =>
              (window.location.href = `/admin/users/${row.original.id}`)
            }
            className="px-3 py-1 rounded text-sm border border-[#c6c5b9]/50 text-gray-200 hover:bg-[#c6c5b9]/30"
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
    <div className="p-6 text-[#393d3f]">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">User Management</h1>
        <p className="text-[#546a7b]">Manage user accounts and permissions</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        {/* Search */}
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1); // Reset to first page
          }}
          className="flex-1 rounded-xl border border-[#c6c5b9]/50 bg-[#c6c5b9]/30 px-4 py-2 text-sm text-gray-200 placeholder:text-[#546a7b]"
        />

        {/* Role Filter */}
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-[#c6c5b9]/50 bg-[#c6c5b9]/30 px-4 py-2 text-sm text-gray-200"
        >
          <option value="">All Roles</option>
          <option value="CUSTOMER">Customer</option>
          <option value="ADMIN">Admin</option>
          <option value="EXPORTER">Exporter</option>
          <option value="CLEARING_AGENT">Clearing Agent</option>
          <option value="FINANCE_PARTNER">Finance Partner</option>
        </select>

        {/* KYC Filter */}
        <select
          value={kycFilter}
          onChange={(e) => {
            setKycFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-[#c6c5b9]/50 bg-[#c6c5b9]/30 px-4 py-2 text-sm text-gray-200"
        >
          <option value="">All KYC Status</option>
          <option value="NONE">Not Submitted</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Stats */}
      <div className="mb-4 text-sm text-[#546a7b]">
        Showing {users.length} of {total} users
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-[#546a7b]">Loading...</div>
      ) : (
        <>
          <div className="rounded-2xl border border-[#c6c5b9]/50 bg-[#c6c5b9]/20 overflow-hidden">
            <table className="min-w-full divide-y divide-white/10">
              <thead className="bg-[#c6c5b9]/20">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-6 py-3 text-left text-xs font-medium text-[#546a7b] uppercase tracking-wider cursor-pointer hover:bg-[#c6c5b9]/20"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        <div className="flex items-center gap-2">
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {header.column.getIsSorted() && (
                            <span>
                              {header.column.getIsSorted() === "desc"
                                ? "v"
                                : "^"}
                            </span>
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="divide-y divide-white/10">
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="hover:bg-[#c6c5b9]/20">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="mt-4 flex justify-between items-center">
            <div className="text-sm text-[#546a7b]">
              Page {page} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 rounded border border-[#c6c5b9]/50 text-gray-200 hover:bg-[#c6c5b9]/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="px-4 py-2 rounded border border-[#c6c5b9]/50 text-gray-200 hover:bg-[#c6c5b9]/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {/* Role Change Modal */}
      {roleChangeModal.open && roleChangeModal.user && (
        <RoleChangeModal
          user={roleChangeModal.user}
          onClose={() => setRoleChangeModal({ open: false, user: null })}
          onSuccess={() => {
            setRoleChangeModal({ open: false, user: null });
            loadUsers();
          }}
        />
      )}
    </div>
  );
}

