#!/bin/bash
# enroll_arkhe_keys.sh — Registra chaves da Catedral no firmware UEFI
sudo efi-updatevar -f /etc/arkhe/keys/cathedral-db.auth db
sudo efi-updatevar -f /etc/arkhe/keys/cathedral-kek.auth KEK
sudo efi-updatevar -f /etc/arkhe/keys/cathedral-pk.auth PK

echo "🔐 Chaves da Catedral registradas no UEFI Secure Boot"
echo "   Apenas binários assinados pela Catedral serão executados."
