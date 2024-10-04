from xwatc_zwei.monster import Monster, Attacke, Einheit

def kampf(kämpfer: list[Monster]):
    for x in kämpfer:
        z=x.mache_einheit()
        print (z)

def angriff (attacke: Attacke, attaceuer: Einheit, ziel: Einheit):
    schaden = attaceuer.stärke + attacke.schaden
    ziel.lp -= schaden


Tadd = Monster("David",5,6,50, [Attacke("Schwert", 12), Attacke("Keule", 5)])
Kadd = Monster("Gabid",3,7,24, [Attacke("Schwert", 9), Attacke("Keule", 9)])
print(Tadd)
print(Kadd)
kampf([Tadd, Kadd])
