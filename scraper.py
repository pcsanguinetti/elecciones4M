from diario import *
import pandas as pd

todos = pd.read_csv("data/todos.csv", index_col=[0])
belicas = pd.read_csv("data/belicas.csv", index_col=[0])
noesunaguerra = pd.read_csv("data/noesunaguerra.csv", index_col=[0])
with open("data/pattern.txt", encoding="UTF-8") as f:
    pattern = f.read()

confi = Diario("El Confidencial", "https://www.elconfidencial.com/tags/temas/elecciones-madrid-21191", tag="article")
abc = Diario("ABC", "https://www.abc.es/elecciones/elecciones-madrid/", class_="cuerpo-articulo")
elpais = Diario("El País", "https://elpais.com/espana/elecciones-madrid/", complemento_url="https://elpais.com", tag="h2")
elmundo = Diario("El Mundo", "https://www.elmundo.es/elecciones/elecciones-madrid.html", tag="div", class_="ue-c-cover-content__main")
razon = Diario("La Razón", "https://www.larazon.es/tags/elecciones-comunidad-de-madrid/", tag="article")
diarioes = Diario("eldiario.es", "https://www.eldiario.es/temas/elecciones-madrid-2021/", class_="ni-title")
espanol = Diario("El Español", "https://www.elespanol.com/temas/elecciones_comunidad_madrid_4m/", complemento_url="https://www.elespanol.com", tag="article")
publico = Diario("Público", "https://www.publico.es/tag/elecciones-madrid/", complemento_url="https://www.publico.es/", tag="article")

diarios = [confi, abc, elpais, elmundo, razon, diarioes, espanol, publico]

todos_antes = len(todos)
belicas_antes = len(belicas)

dfs = {"todos" : todos}
dfs_belicas = {"belicas" : belicas}
dfs_guerra = {"guerra" : noesunaguerra}

for diario in diarios:
    dfs[diario.nombre] = diario.scrape()
    dfs_belicas[diario.nombre] = filtrar_belicas(dfs[diario.nombre], pattern)
    dfs_guerra[diario.nombre] = rearrange(dfs_belicas[diario.nombre])
    
todos = pd.concat([df for df in dfs.values()]).reset_index(drop=True)
belicas = pd.concat([df for df in dfs_belicas.values()]).reset_index(drop=True)
noesunaguerra = pd.concat([df for df in dfs_guerra.values()]).reset_index(drop=True)

errores = len(todos[todos["Titular"]=="error"])
print("Se agregaron {} entradas".format(len(todos)-todos_antes))
print("Se agregaron {} palabras bélicas".format(len(belicas)-belicas_antes))
print("Errores de parsing: ", errores)

todos.drop_duplicates(["Titular", "Diario"], inplace=True)
todos = todos.drop(todos[todos["Titular"]=="error"].index)
todos.sort_values(by="Fecha", inplace = True)

with open("data/blacklist.txt") as b:
    blacklist = b.read().splitlines() 

belicas = belicas[~belicas["Titular"].isin(blacklist)]
belicas.drop_duplicates(["Palabra", "Titular", "Diario"], inplace=True)
belicas.sort_values(by="Fecha", inplace = True)
noesunaguerra.drop_duplicates(["todo"], inplace=True)

df1 = belicas.groupby(by=["Diario"])["Palabra"].count().reset_index()
df2 = todos.groupby(by=["Diario"]).agg({
    "Titular" : "count",
    "Pos" : "mean",
    "Neg" : "mean",
    "Neu" : "mean"}).reset_index()

resumen = pd.merge(df1, df2, on="Diario")

resumen["Porcentaje"] = resumen["Palabra"] / resumen["Titular"] * 100
resumen.sort_values("Porcentaje", ascending=False, inplace=True)

todos.to_csv("data/todos.csv")
belicas.to_csv("data/belicas.csv")
resumen.to_csv("data/resumen.csv")
noesunaguerra.to_csv("data/noesunaguerra.csv")