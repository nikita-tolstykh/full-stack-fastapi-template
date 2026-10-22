import { Link } from "@tanstack/react-router"
import { ShieldX } from "lucide-react"

import { Button } from "@/components/ui/button"

const Forbidden = () => {
  return (
    <div
      className="flex flex-col items-center justify-center text-center py-24"
      data-testid="forbidden"
    >
      <div className="rounded-full bg-muted p-4 mb-4">
        <ShieldX className="h-8 w-8 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-bold mb-2">Access denied</h1>
      <p className="text-muted-foreground mb-4">
        Your role doesn't give you access to this page. Ask an admin if you need
        it.
      </p>
      <Link to="/">
        <Button>Go to dashboard</Button>
      </Link>
    </div>
  )
}

export default Forbidden
