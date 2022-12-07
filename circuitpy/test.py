import time
import json
import asyncio
import board
import neopixel
import canio
from pin import pin

# Load the config file
f = open ('config.json', "r")
config = json.loads(f.read())
f.close()

async def blink(pin):
    try:
        with neopixel.NeoPixel(pin, 144, brightness=1.0, auto_write=True, pixel_order=neopixel.GRB) as pixels:
            pixels.fill((255, 75, 2))
            await asyncio.sleep(0.45)
            pixels.fill((0, 0, 0))
            await asyncio.sleep(0.45)
    except Exception as e:
        #print(e)
        return

async def blink_faded(pin):
    try:
        with neopixel.NeoPixel(pin, 144, brightness=1.0, auto_write=True, pixel_order=neopixel.GRB) as pixels:
            pixels.fill((255, 75, 2))
            await asyncio.sleep(0.45)
            # Fade out
            seq = [x/10 for x in range(10, -1, -1)]
            for i in seq:
                pixels.fill((255*i, 75*i, 2*i))
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.35)
    except Exception as e:
        #print(e)
        return

async def HazardWarningReq(group):
    for port_use in group['ports']:
        for port in config['ports']:
            if port_use == port['name']:
                 asyncio.create_task(blink(pin(port['pin1'])))
#     print('end time', time.monotonic())
#     print()

async def TurnLightReq(group):
    for port_use in group['ports']:
        for port in config['ports']:
            if port_use == port['name']:
                 asyncio.create_task(blink_faded(pin(port['pin1'])))
#     print('end time', time.monotonic())
#     print()

func_callback = {
    "HazardWarningReq" : HazardWarningReq,
    "RightTurnLightReq" : TurnLightReq,
    "LeftTurnLightReq" : TurnLightReq
}

async def CANListener(can):
    listener = can.listen(timeout=0)
    old_bus_state = None
    
    while True:
        #print(time.monotonic())
        bus_state = can.state
        if bus_state != old_bus_state:
            print(f"Bus state changed to {bus_state}")
            old_bus_state = bus_state
        
        message = listener.receive()
        if message is not None:
            for group in config['groups']:
                if message.id == group['id'] and message.data == bytearray(group['data']):
                    print(group['description'], time.monotonic())
                    await func_callback[group['name']](group)
        # Setting the delay to 0 provides an optimized path to allow other tasks to run. 
        await asyncio.sleep(0) # Free up the resource for a while. 

async def main():
    tasks = []
    
    # Initialize CAN bus
    can = canio.CAN(rx=board.CAN_RX, tx=board.CAN_TX, baudrate=500_000, auto_restart=True)

    tasks.append(asyncio.create_task(CANListener(can)))
    await asyncio.gather(*tasks)

asyncio.run(main())


