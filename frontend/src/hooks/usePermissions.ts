import type { Permission } from "@/client"
import useAuth from "./useAuth"

/**
 * What the signed-in user may do. Permissions come from GET /users/me,
 * so the role -> permission map lives only in the backend.
 */
const usePermissions = () => {
  const { user } = useAuth()

  const can = (permission: Permission) =>
    user?.permissions.includes(permission) ?? false

  return { can, isLoaded: user != null }
}

export default usePermissions
