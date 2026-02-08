"use client";

import { useLogout } from "@/lib/hooks/useLogout";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

/**
 * LogoutButton Component
 * Styled with dark orange theme
 */
export default function LogoutButton() {
    const { logout, isLoading } = useLogout();

    return (
        <Button
            onClick={logout}
            disabled={isLoading}
            className="min-w-[120px] bg-[#D65A31] hover:bg-[#c14a28] text-white transition-colors"
        >
            {isLoading ? (
                <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing out...
                </>
            ) : (
                "Sign Out"
            )}
        </Button>
    );
}
