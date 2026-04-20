"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Briefcase,
  Inbox,
  LayoutDashboard,
  Settings,
  Users,
} from "lucide-react"

import type { NavSection } from "@/lib/types/nav"
import { cn } from "@/lib/utils"

const sections: NavSection[] = [
  {
    items: [
      { title: "Dashboard", href: "/", icon: LayoutDashboard },
      { title: "职位管理", href: "/jobs", icon: Briefcase },
      { title: "分拣工作台", href: "/workbench", icon: Inbox },
      { title: "候选人", href: "/candidates", icon: Users },
    ],
  },
  {
    title: "系统",
    items: [
      {
        title: "系统设置",
        href: "/settings",
        icon: Settings,
        disabled: true,
      },
    ],
  },
]

export function SidebarNav() {
  const pathname = usePathname()

  return (
    <nav className="flex flex-col gap-6 px-3 py-4">
      {sections.map((section, idx) => (
        <div key={idx} className="flex flex-col gap-1">
          {section.title && (
            <span className="mb-1 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {section.title}
            </span>
          )}
          {section.items.map((item) => {
            const Icon = item.icon
            const active =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.disabled ? "#" : item.href}
                aria-disabled={item.disabled}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  item.disabled && "pointer-events-none opacity-50"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.title}</span>
              </Link>
            )
          })}
        </div>
      ))}
    </nav>
  )
}
