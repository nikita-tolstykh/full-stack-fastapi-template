import type { ReactNode } from "react"

import type { Permission } from "@/client"
import usePermissions from "@/hooks/usePermissions"
import Forbidden from "./Forbidden"

interface RequirePermissionProps {
  permission: Permission
  children: ReactNode
}

/** Renders the page only if the user's role grants `permission`. */
const RequirePermission = ({
  permission,
  children,
}: RequirePermissionProps) => {
  const { can, isLoaded } = usePermissions()

  if (!isLoaded) {
    return null
  }
  return can(permission) ? children : <Forbidden />
}

export default RequirePermission
