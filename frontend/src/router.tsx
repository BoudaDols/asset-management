import { createBrowserRouter, Navigate } from "react-router-dom"
import Layout from "@/components/Layout"
import CatalogPage from "@/pages/CatalogPage"
import AssetsPage from "@/pages/AssetsPage"
import ImportPage from "@/pages/ImportPage"
import ReportsPage from "@/pages/ReportsPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/catalog" replace /> },
      { path: "catalog", element: <CatalogPage /> },
      { path: "assets", element: <AssetsPage /> },
      { path: "import", element: <ImportPage /> },
      { path: "reports", element: <ReportsPage /> },
    ],
  },
])
