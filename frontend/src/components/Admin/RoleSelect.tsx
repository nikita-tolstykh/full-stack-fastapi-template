import type { Role } from "@/client"
import { FormControl } from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Record<Role, …> makes TypeScript flag this list when the API adds a role
const ROLE_LABELS: Record<Role, string> = {
  member: "Member",
  manager: "Manager",
  admin: "Admin",
}

export const ROLES = Object.keys(ROLE_LABELS) as [Role, ...Role[]]

interface RoleSelectProps {
  value?: Role
  onChange: (role: Role) => void
}

export const RoleSelect = ({ value, onChange }: RoleSelectProps) => (
  <Select value={value} onValueChange={(role) => onChange(role as Role)}>
    <FormControl>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a role" />
      </SelectTrigger>
    </FormControl>
    <SelectContent>
      {ROLES.map((role) => (
        <SelectItem key={role} value={role}>
          {ROLE_LABELS[role]}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)
