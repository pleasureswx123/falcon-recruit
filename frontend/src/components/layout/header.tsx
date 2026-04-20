"use client"

import { usePathname } from "next/navigation"
import { Bell, LogOut, User } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const titleMap: Record<string, string> = {
  "/": "Dashboard",
  "/jobs": "职位管理",
  "/workbench": "分拣工作台",
  "/candidates": "候选人",
  "/settings": "系统设置",
}

function resolveTitle(pathname: string): string {
  if (titleMap[pathname]) return titleMap[pathname]
  const prefix = Object.keys(titleMap)
    .filter((k) => k !== "/" && pathname.startsWith(k))
    .sort((a, b) => b.length - a.length)[0]
  return prefix ? titleMap[prefix] : "未知页面"
}

export function Header() {
  const pathname = usePathname()
  const title = resolveTitle(pathname)

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold">{title}</h1>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="通知">
          <Bell className="h-4 w-4" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 px-2">
              <Avatar className="h-7 w-7">
                <AvatarImage src="" alt="HR" />
                <AvatarFallback className="text-xs">HR</AvatarFallback>
              </Avatar>
              <span className="text-sm">管理员</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>我的账号</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              个人资料
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <LogOut className="mr-2 h-4 w-4" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
