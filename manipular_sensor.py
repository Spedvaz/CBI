import sys
from pymodbus.client import ModbusTcpClient

activar = not(
    len(sys.argv) > 1 and sys.argv[1] == "restaurar"
    )
cliente = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)

try:
    if not cliente.connect():
        print("No se ha podido conectar con el servidor")
    else:
        respuesta = cliente.write_registers(
            address=3,
            values=[1 if activar else 0, 600],
            device_id=1
        )

        if respuesta.isError():
            print("Error:", respuesta)
        elif activar:
            print("Sensor manipulado: publicara 60.0 ºC constantes.")
        else:
            print("Sensor restaurado: publicara la temperatura real")
finally:
    cliente.close()