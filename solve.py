#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

from ortools.sat.python import cp_model
import pandas as pd

def get_successive_dates(dates):
    successives_dates = []
    for d1 in dates:
        for d2 in dates:
            if d1 > d2 and d1.week == d2.week:
                successives_dates.append((d1, d2))
    return successives_dates

parser = argparse.ArgumentParser(
                    prog='Inscription-Aterlier',
                    description='Trouve une solution pour assigner des ateliers à partir d\'une liste de disponibilités')
parser.add_argument('filename')
args = parser.parse_args()

filename = Path(args.filename)
if not filename.exists():
    print(f"The file '{filename}' does not exists.")
    exit()

with open("var.json") as f:
    variables = json.load(f)

df = pd.read_excel(filename, index_col=0)
model = cp_model.CpModel()
personnes = df.columns.tolist()
dates = df.index.tolist()

print(f"{personnes=}")
print(f"{dates=}")

horaire = {p: {} for p in personnes}
for d in dates:
    for p in personnes:
        if df.at[d, p] == 0:
            horaire[p][d] = model.new_constant(0)
        elif df.at[d, p] == 1:
            horaire[p][d] = model.new_bool_var(f"schedule_{p}_{d}")
        elif df.at[d, p] > 1:
            horaire[p][d] = model.new_int_var_from_domain(cp_model.Domain.from_intervals([[0, 0], [df.at[d, p], df.at[d, p]]]), f"schedule_{p}_{d}")

# max 4 places par date
for d in dates:
    model.add(sum([horaire[p][d] for p in personnes]) <= variables["place_par_date"])

# chaque personne minimum 3x ou nombre de places demandée
for p in personnes:
    model.add(sum([horaire[p][d] for d in dates]) >= min(variables["min_par_personne"]*df[p].max(), int(df[p].sum())))

# chaque personne maximum 5x
for p in personnes:
    model.add(sum([horaire[p][d] for d in dates]) <= variables["max_par_personne"])

# une personne ne peut pas venir 2x la même semaine
for d1, d2 in get_successive_dates(dates):
    for p in personnes:
        model.add(horaire[p][d1] + horaire[p][d2] <= 1)

# minimise le nombre de dates pour une personne -> rend le nombre d'ateliers équitables
max_dates = model.new_int_var(0, len(dates), "max_dates")
model.add_min_equality(max_dates, [sum(horaire[p].values()) for p in personnes])
model.minimize(max_dates)
print("Calcul d'une solution...")

solver = cp_model.CpSolver()
solver.solve(model)

if solver.response_proto.status in [cp_model.CpSolverStatus.MODEL_INVALID, cp_model.CpSolverStatus.INFEASIBLE]:
    print(f"Pas de réponse trouvée, erreur: {solver.response_proto.status}")
    exit()
elif solver.response_proto.status == cp_model.CpSolverStatus.OPTIMAL:
    print("Solution trouvée, voir fichier de solution !")

for d in dates:
    for p in personnes:
        df.at[d, p] = solver.value(horaire[p][d])

writer = pd.ExcelWriter(filename.stem + "-solution.ods", engine='odf')
df.index = df.index.map(lambda x: x.strftime("%d/%m/%Y"))
df.to_excel(writer, sheet_name="Feuille1")
writer.close()

for p in personnes:
    print(p, end="\t")
    for d in dates:
        if solver.value(horaire[p][d]):
            print(f"{d.strftime("%d/%m/%Y")}", end=" ")
    print()
