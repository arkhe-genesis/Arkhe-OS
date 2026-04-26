import * as React from "react"
import { cn } from "../../lib/utils"

export const Switch = ({ checked, onCheckedChange, ...props }: any) => (
  <button type="button" role="switch" aria-checked={checked} onClick={() => onCheckedChange?.(!checked)} {...props} />
)
