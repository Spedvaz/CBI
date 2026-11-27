from pymodbus.client import ModbusTcpClient

cliente = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)

try: 
    if not cliente.connect():
        print("No se ha podido conectar con el servidor")
    else:
        print("Conexion establecida")

        respuesta = cliente.read_holding_registers(
            address=0,
            count=1,
            device_id=1
        )

        if respuesta.isError():
            print("Error al leer:", respuesta)
        else:
            print("Valor del registro 0:", respuesta.registers[0])
finally:
    cliente.close()