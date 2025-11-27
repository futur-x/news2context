import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

interface LayoutProps {
    children: ReactNode
}

function Layout({ children }: LayoutProps) {
    const location = useLocation()

    const isActive = (path: string) => location.pathname === path

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h1 className="logo">News2Context</h1>
                    <p className="tagline">Knowledge Base Platform</p>
                </div>

                <nav className="nav">
                    <Link
                        to="/"
                        className={`nav-item ${isActive('/') ? 'active' : ''}`}
                    >
                        <span className="nav-icon">📊</span>
                        <span>Dashboard</span>
                    </Link>

                    <Link
                        to="/settings"
                        className={`nav-item ${isActive('/settings') ? 'active' : ''}`}
                    >
                        <span className="nav-icon">⚙️</span>
                        <span>Settings</span>
                    </Link>
                </nav>

                <div className="sidebar-footer">
                    <div className="version">v2.0.0</div>
                </div>
            </aside>

            <main className="main-content">
                {children}
            </main>
        </div>
    )
}

export default Layout
