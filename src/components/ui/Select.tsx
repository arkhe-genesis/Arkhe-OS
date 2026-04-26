import * as React from "react"
import { cn } from "../../lib/utils"

export const Select = ({ children, ...props }: any) => <div {...props}>{children}</div>
export const SelectTrigger = ({ children, ...props }: any) => <button {...props}>{children}</button>
export const SelectValue = ({ children, ...props }: any) => <span {...props}>{children}</span>
export const SelectContent = ({ children, ...props }: any) => <div {...props}>{children}</div>
export const SelectItem = ({ children, ...props }: any) => <div {...props}>{children}</div>
