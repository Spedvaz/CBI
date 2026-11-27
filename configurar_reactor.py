from pymodbus.client import ModbusTcpClient

cliente = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)

try:
    if not cliente.connect():
        print("No se ha podido conectar con el servidor")
    else:
        escritura = cliente.write_registers(
            address=0,
            values=[600, 600, 800],
            device_id=1
        )

        if escritura.isError():
            print("Error al escribir:", escritura)
        else:
            lectura = cliente.read_holding_registers(
                address=0,
                count=3,
                device_id = 1
            )

            if lectura.isError():
                print("Error al leer:", lectura)
            else:
                valores = lectura.registers
                print("Temperatura medida:", valores[0] / 10, "ºC")
                print("Temperatura deseada:", valores[1] / 10, "ºC")
                print("Umbral de alarma:", valores[2] / 10, "ºC")
finally: 
    cliente.close()
