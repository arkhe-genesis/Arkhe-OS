import math

def cyclic_diff(t1, t2):
    return (t1 - t2 + math.pi) % (2 * math.pi) - math.pi

print(cyclic_diff(0.05, 6.20)) # should be ~0.13
print(cyclic_diff(6.20, 0.05)) # should be ~-0.13
