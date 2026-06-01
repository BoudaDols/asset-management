import { NavLink, Outlet } from "react-router-dom"
import { FolderTree, Package, Upload, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/catalog", label: "Catalogue", icon: FolderTree },
  { to: "/assets", label: "Actifs", icon: Package },
  { to: "/import", label: "Importation", icon: Upload },
  { to: "/reports", label: "Rapports", icon: BarChart3 },
]

export default function Layout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col">
        <div className="p-4 border-b border-border">
          <h1 className="text-lg font-bold text-primary">
            Gestion des Actifs
          </h1>
          <p className="text-xs text-muted-foreground">Système municipal</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
