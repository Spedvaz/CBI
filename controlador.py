import time
from pymodbus.client import ModbusTcpClient

cliente = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)
refrigeracion = False

try:
    if not cliente.connect():
        print("No se ha podido conectar con el servidor")
    else:
        print("Controlador iniciado. Ctrl+C para desconectarlo")

        while True:
            respuesta = cliente.read_holding_registers(
                address=0,
                count=3,
                device_id=1
            )

            if respuesta.isError():
                print("Error al leer:", respuesta)
                break

            medida, objetivo, umbral = [
                valor / 10 for valor in respuesta.registers
            ]

            if medida >= objetivo + 1:
                refrigeracion = True
            elif medida <= objetivo -1:
                refrigeracion = False

            escritura = cliente.write_coil(
                address=0,
                value=refrigeracion,
                device_id=1
            )

            if escritura.isError():
                print("Error al enviar la orden:", escritura)
                break

            estado ="ACTIVA" if refrigeracion else "APAGADA"
            alarma ="ACTIVA" if medida >= umbral else "NORMAL"

            print(
                f"Medida : {medida:1f} ºC |"
                f"Refrigeración: {estado} | Alarma: {alarma}"
            )

            time.sleep(1)
except KeyboardInterrupt:
    print("\nControlador detenido")
finally:
    cliente.close()