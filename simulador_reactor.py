import time
from pymodbus.client import ModbusTcpClient

cliente = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)
temperatura_real = 60.0

try:
    if not cliente.connect():
        print("No se ha podido conectar con el servidor")
    else:
        print("Simulador iniciado. Ctrl+C para detener")

        inicio = cliente.write_registers(
            address=3,
            values=[0,600],
            device_id=1
        )

        if inicio.isError():
            raise RuntimeError(f"Error al preparar el sensor: {inicio}")

        print("Simulador iniciado. Ctrl+C para detenerlo")

        while True:
            orden = cliente.read_coils(
                address=0,
                count=1,
                device_id=1
            )

            sensor = cliente.read_holding_registers(
                address=3, count=2, device_id=1
            )

            if orden.isError() or sensor.isError():
                print("Error al consultar los datos del servidor")
                break

            refrigeracion = orden.bits[0]
            manipulado = sensor.registers[0] == 1

            if refrigeracion:
                temperatura_real -= 0.6
            else:
                temperatura_real += 0.4

            temperatura_real = round(max(20.0, temperatura_real), 1)

            if manipulado:
                medicion = sensor.registers[1]
            else:
                medicion = int(round(temperatura_real*10))

            escritura = cliente.write_register(
                address=0,
                value=medicion,
                device_id=1
            )

            if escritura.isError():
                print("Error al publicar la medicion:", escritura)
                break

            estado = "ACTIVA" if refrigeracion else "APAGADA"
            modo = "MANIPULADO" if manipulado else "NORMAL"

            print(
                f"Real: {temperatura_real:.1f} ºC |"
                f"Medida: {medicion / 10:.1f} ºC |"
                f"Refrigeracion: {estado} | Sensor: {modo}"
            )

            time.sleep(1)

except KeyboardInterrupt:
    print("\nSimulador detenido")
finally:
    cliente.close()