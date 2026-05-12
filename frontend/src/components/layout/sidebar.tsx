import Image from "next/image"
import { SidebarNav } from "@/components/layout/sidebar-nav"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 flex-col border-r bg-background">
        <div className="border-b border-sidebar-border py-4 pt-0">
            <div className="flex flex-col gap-3">
                <div className="flex h-14 shrink-0 items-center justify-center bg-black px-4 py-2 border-b border-sidebar-border">
                    <div className="relative w-[80%]" style={{aspectRatio: '120/26'}}>
                        <Image
                            src="/logo.svg"
                            alt="莱博塔Logo"
                            fill
                            className="object-contain"
                            priority
                        />
                    </div>
                </div>
                <div className="flex items-center flex-col">
                    <span className="text-sm font-semibold text-sidebar-foreground">猎鹰 - 智能招聘管理平台</span>
                    <span className="text-xs text-sidebar-foreground/60">Smart Recruitment Platform</span>
                </div>
            </div>
        </div>
      {/* <div className="flex h-14 shrink-0 items-center px-4">
        <Logo />
      </div>
      <Separator /> */}
      <ScrollArea className="flex-1">
        <SidebarNav />
      </ScrollArea>
      <Separator />
      <div className="px-4 py-3 text-[11px] text-muted-foreground">
        v0.1.0 · © 2026 北京莱博塔科技有限公司
      </div>
    </aside>
  )
}
