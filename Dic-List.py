aliens=[]

for i in range(31):
    new= {'color': 'green', 'points': 5, 'speed': 'slow'}
    aliens.append(new)

for a in aliens[:5]: 
    print(a) 
print("...")

print("Total number of aliens: " + str(len(aliens)))