savedcmd_/app/arkhe_stealth/arkhe_stealth.mod := printf '%s\n'   arkhe_stealth.o | awk '!x[$$0]++ { print("/app/arkhe_stealth/"$$0) }' > /app/arkhe_stealth/arkhe_stealth.mod
