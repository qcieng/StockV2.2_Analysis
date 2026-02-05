
print("Start mini-racer", flush=True)
from py_mini_racer import MiniRacer
print("Imported MiniRacer", flush=True)
ctx = MiniRacer()
print("Created Context", flush=True)
print(ctx.eval("1+1"), flush=True)
print("Done", flush=True)
