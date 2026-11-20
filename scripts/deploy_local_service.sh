#!/usr/bin/env bash
# Apply the reviewed localhost service unit, retaining a rollback copy.
# Run explicitly with sudo after reviewing services/jarvis-core.service.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo 'Run this script with sudo to install and restart jarvis-core.service.' >&2
  exit 1
fi
jarvis_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
jarvis_unit="$jarvis_root/services/jarvis-core.service"
jarvis_target=/etc/systemd/system/jarvis-core.service
[[ -x "$jarvis_root/venv/bin/python" ]] || { echo 'Project Python environment is missing.' >&2; exit 1; }
systemd-analyze verify "$jarvis_unit"
jarvis_backup_dir=$(mktemp -d /var/backups/jarvis-os-service.XXXXXX)
jarvis_had_unit=false
if [[ -f "$jarvis_target" ]]; then
  cp -p -- "$jarvis_target" "$jarvis_backup_dir/jarvis-core.service"
  jarvis_had_unit=true
fi
rollback() {
  echo 'Service validation failed; restoring the prior unit.' >&2
  if [[ "$jarvis_had_unit" == true ]]; then
    cp -p -- "$jarvis_backup_dir/jarvis-core.service" "$jarvis_target"
    systemctl daemon-reload
    systemctl restart jarvis-core.service || true
  else
    systemctl stop jarvis-core.service || true
    # Leave the reviewed new unit on disk, stopped, for inspection.
  fi
}
trap rollback ERR
install -m 0644 -- "$jarvis_unit" "$jarvis_target"
systemctl daemon-reload
systemctl restart jarvis-core.service
jarvis_ready=false
for ((attempt=0; attempt<30; attempt++)); do
  if curl --noproxy '*' --fail --silent --max-time 2 \
      -H 'X-Jarvis-Client: dashboard' \
      http://127.0.0.1:8000/api/active-desktop/status > /dev/null; then
    jarvis_ready=true
    break
  fi
  sleep 1
done
[[ "$jarvis_ready" == true ]]
trap - ERR
printf 'JARVIS updated: http://127.0.0.1:8000\nPrevious unit saved in: %s\n' "$jarvis_backup_dir"
