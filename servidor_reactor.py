#!/usr/bin/env python3
"""
Servidor Modbus TCP del reactor = banco de registros compartido.

Es el servidor central al que se conectan el controlador y el simulador de la
Parte A. Aqui se guarda el estado del reactor; la logica vive en los clientes
(como en vuestra Parte A). Igual que en la industria: un esclavo Modbus TCP en
el puerto 5020 con direccionamiento directo (device_id 1).

Mapa de registros (el mismo que usa la Parte A):
    HR 0  -> temperatura medida   (C x 10)
    HR 1  -> consigna             (C x 10) = 600  (60.0 C)
    HR 2  -> umbral de alarma     (C x 10) = 800  (80.0 C)
    HR 3  -> flag sensor manipulado (ataque de la Parte A)
    HR 4  -> valor manipulado     (C x 10) = 600
    Coil 0 -> orden de refrigeracion (0/1)

Diferencia clave frente a la Parte A: escucha en 0.0.0.0 (toda la red), para
que el controlador pueda conectarse desde OTRA VM y el MITM pueda interceptar.

Ejecutar en la VM "planta" (junto con simulador_reactor.py):
    python3 servidor_reactor.py          # puerto 5020, no necesita root
"""
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server import StartTcpServer

HOST = "0.0.0.0"
PORT = 5020

# Valores iniciales = los que fija configurar_reactor.py (medida, consigna, umbral)
# mas los de simulador_reactor.py (flag manipulado, valor manipulado).
HOLDING_INICIAL = [600, 600, 800, 0, 600] + [0] * 11   # HR0..HR15
COILS_INICIAL = [0] * 16

# zero_mode=True -> la direccion del cliente es el indice real (addr 0 = HR0).
store = ModbusSlaveContext(
    co=ModbusSequentialDataBlock(0, COILS_INICIAL),
    hr=ModbusSequentialDataBlock(0, HOLDING_INICIAL),
    zero_mode=True,
)
context = ModbusServerContext(slaves=store, single=True)


if __name__ == "__main__":
    print(f"[SERVIDOR] Banco de registros Modbus TCP en {HOST}:{PORT}")
    print("[SERVIDOR] Ctrl+C para detener.")
    StartTcpServer(context=context, address=(HOST, PORT))
