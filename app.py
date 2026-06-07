import pandas as pd
import streamlit as st
import plotly.express as px
import gdown

#setea valor del titulo de la pagina

st.set_page_config(page_title="Censo Uruguay 2023", layout="wide")

# Creamos un diccionario con coordenadas de cada departamento para luego usarlas en un mapa

COORDS = {
    "Montevideo":     (-34.9011, -56.1645),
    "Artigas":        (-30.4000, -56.4800),
    "Canelones":      (-34.5200, -56.0100),
    "Cerro Largo":    (-32.3700, -54.1700),
    "Colonia":        (-34.4700, -57.8400),
    "Durazno":        (-33.3800, -56.5200),
    "Flores":         (-33.5700, -56.8900),
    "Florida":        (-34.0900, -56.2100),
    "Lavalleja":      (-34.4200, -55.2300),
    "Maldonado":      (-34.9000, -54.9500),
    "Paysandú":       (-32.3200, -58.0800),
    "Río Negro":      (-32.7500, -57.9900),
    "Rivera":         (-30.9000, -55.5500),
    "Rocha":          (-34.4800, -54.3400),
    "Salto":          (-31.3800, -57.9600),
    "San José":       (-34.3400, -56.7100),
    "Soriano":        (-33.5300, -58.0200),
    "Tacuarembó":     (-31.7200, -55.9800),
    "Treinta y Tres": (-33.2300, -54.3800),
}

# seteamos arrays con valores

SIN_DATO = ["No aplica", "No sabe / Sin dato", "No relevado", "Sin dato"]

NIVELES_ORDEN = [
    "Educación Inicial o Preescolar", "Primaria común", "Primaria especial",
    "Educación media básica / Ciclo Básico",
    "Educación media superior / Bachillerato",
    "Capacitaciones UTU (sin CB ni Bach.)",
    "Magisterio o profesorado", "Terciario no universitario",
    "Universidad o similar", "Posgrado (diploma, maestría, doctorado)"
]

# cargamos el archivo CSV en memosria con las columnas que vamos a usar
# al final saque mas columnas de las que ya había sacado con Pandas para crear el archivo
@st.cache_data
def cargar_datos():
    cols = [
        "DEPARTAMENTO", "SEXO AL NACER",
        "NIVEL EDUCATIVO CURSANDO ACTUALMENTE",
        "NIVEL MÁS ALTO QUE CURSÓ",
        "REGIÓN", "AREA", "ACCESO A INTERNET"
    ]

    #false para usar el arvhivo desde processed o true para tomarlo desde drive (como es muy grande no sube a Git)
    usar_drive = True

    if usar_drive:
        url = "https://drive.google.com/uc?id=1rfYhJATQoJ4S6dfQfFG810tMUTXxgGTa"
        gdown.download(url, "censo_procesado_todas_las_personas.csv", quiet=True)
        ruta = "censo_procesado_todas_las_personas.csv"
    else:
        ruta = "data/processed/censo_procesado_todas_las_personas.csv"

    df = pd.read_csv(ruta, usecols=cols, dtype=str)


    # mapeamos dos columnas que no habiamos mapeado al crear el csv final.
    mapa_region = {"1": "Montevideo", "2": "Interior +5000 hab.",
                   "3": "Interior -5000 hab.", "4": "Zona rural"}
    mapa_area = {"1": "Urbano", "2": "Rural"}
    df["REGIÓN"] = df["REGIÓN"].map(mapa_region).fillna("Sin dato")
    df["AREA"]   = df["AREA"].map(mapa_area).fillna("Sin dato")

    # Pre agregar en tablas mas pequeñas, como el archivo es muy grande, se crea una lista dimm con la columnas que queremos
    # utilizar, y luego con las funcion agg, se calcula las diferentes combinacions y se guarda en tablas directamente el numero de la cantidad de tuplas que cumplen la combinacion
    # por lo que al filtrar, no busca en los millones de registros del archivo siempre, sino que consulta las tablas mas pequeñas

    dims = ["DEPARTAMENTO", "SEXO AL NACER", "ÁREA" if "ÁREA" in df.columns else "AREA",
            "REGIÓN", "NIVEL MÁS ALTO QUE CURSÓ",
            "NIVEL EDUCATIVO CURSANDO ACTUALMENTE", "ACCESO A INTERNET"]
    dims = [d for d in dims if d in df.columns]
    area_col = "ÁREA" if "ÁREA" in df.columns else "AREA"

    agg = df.groupby(dims, dropna=False).size().reset_index(name="Personas")
    return agg, area_col

agg, area_col = cargar_datos()
total_personas = int(agg["Personas"].sum())

# SIDEBAR
st.sidebar.markdown("## 🇺🇾 Censo Uruguay 2023")

st.sidebar.markdown("### Departamentos")
col_m, col_d = st.sidebar.columns(2)
marcar_todos    = col_m.button("✅ Todos")
desmarcar_todos = col_d.button("❌ Ninguno")

departamentos = sorted(agg["DEPARTAMENTO"].dropna().unique().tolist())


if "dpto_inicializado" not in st.session_state:
    for d in departamentos:
        st.session_state[f"dpto_{d}"] = True
    st.session_state["dpto_inicializado"] = True

# checks box actualizan session_state directamente con la key del checkbox
if marcar_todos:
    for d in departamentos:
        st.session_state[f"dpto_{d}"] = True
if desmarcar_todos:
    for d in departamentos:
        st.session_state[f"dpto_{d}"] = False

dpto_sel = []
for d in departamentos:
    if st.sidebar.checkbox(d, key=f"dpto_{d}"):
        dpto_sel.append(d)

st.sidebar.markdown("### Área")
areas = sorted(agg[area_col].dropna().unique().tolist())
area_sel = [a for a in areas if st.sidebar.checkbox(a, value=True, key=f"area_{a}")]

st.sidebar.markdown("### Sexo al nacer")
sexos = sorted(agg["SEXO AL NACER"].dropna().unique().tolist())
sexo_sel = [s for s in sexos if st.sidebar.checkbox(s, value=True, key=f"sexo_{s}")]

st.sidebar.markdown("### Acceso a internet")
internet_opts = sorted(agg["ACCESO A INTERNET"].dropna().unique().tolist())
internet_sel = [i for i in internet_opts if st.sidebar.checkbox(i, value=True, key=f"inet_{i}")]

#  Filtros
mask = (
    agg["DEPARTAMENTO"].isin(dpto_sel) &
    agg[area_col].isin(area_sel) &
    agg["SEXO AL NACER"].isin(sexo_sel) &
    agg["ACCESO A INTERNET"].isin(internet_sel)
)
fil = agg[mask]
total_fil = int(fil["Personas"].sum())

# Titulo
st.title("📊 Censo Uruguay 2023")
st.markdown(f"Mostrando **{total_fil:,}** personas de un total de **{total_personas:,}**")
st.divider()



# slider nivel educativo
st.subheader("Resumen descriptivo")

niveles_disponibles = [n for n in NIVELES_ORDEN
                       if n in fil["NIVEL MÁS ALTO QUE CURSÓ"].unique()]

if len(niveles_disponibles) >= 2:
    rango_edu = st.select_slider(
        "Filtrar por rango de nivel educativo alcanzado",
        options=niveles_disponibles,
        value=(niveles_disponibles[0], niveles_disponibles[-1])
    )
    idx_min = niveles_disponibles.index(rango_edu[0])
    idx_max = niveles_disponibles.index(rango_edu[1])
    niveles_sel = niveles_disponibles[idx_min:idx_max+1]
else:
    niveles_sel = niveles_disponibles

# fil_edu aplica TODOS los filtros: departamento + área + sexo + internet + slider educativo
fil_edu = fil[fil["NIVEL MÁS ALTO QUE CURSÓ"].isin(niveles_sel)]

# Resumen sobre fil_edu — se actualiza con todos los filtros
st.markdown(
    f"Los valores de abajo describen la **cantidad de personas por departamento** "
    f"con nivel educativo entre **{niveles_sel[0] if niveles_sel else '—'}** "
    f"y **{niveles_sel[-1] if niveles_sel else '—'}**, "
    f"aplicando todos los filtros activos."
)

ppd = fil_edu[~fil_edu["NIVEL MÁS ALTO QUE CURSÓ"].isin(SIN_DATO)] \
      .groupby("DEPARTAMENTO")["Personas"].sum()

if len(ppd) > 0:
    dpto_max = ppd.idxmax()
    dpto_min = ppd.idxmin()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Media",     f"{ppd.mean():,.0f}")
    c2.metric("Mediana",   f"{ppd.median():,.0f}")
    c3.metric(f"Máximo ({dpto_max})",  f"{ppd.max():,.0f}")
    c4.metric(f"Mínimo ({dpto_min})",  f"{ppd.min():,.0f}")
    c5.metric("Desv. Std", f"{ppd.std():,.0f}")
    c6.metric("Rango",     f"{ppd.max()-ppd.min():,.0f}")
    q1, q3 = ppd.quantile(0.25), ppd.quantile(0.75)
    st.markdown(
        f"**Q1:** {q1:,.0f} &nbsp;|&nbsp; **Q3:** {q3:,.0f} &nbsp;|&nbsp; "
        f"**Total:** {int(ppd.sum()):,} personas con nivel seleccionado"
    )
else:
    st.warning("No hay datos para los filtros seleccionados.")

st.divider()

# ── GRÁFICO 1: Educación general ──────────────────────────────────────────────
st.subheader("Nivel educativo más alto cursado")
g1 = (fil_edu[~fil_edu["NIVEL MÁS ALTO QUE CURSÓ"].isin(SIN_DATO)]
      .groupby("NIVEL MÁS ALTO QUE CURSÓ")["Personas"].sum()
      .reset_index().sort_values("Personas", ascending=True))
fig1 = px.bar(g1, x="Personas", y="NIVEL MÁS ALTO QUE CURSÓ", orientation="h",
              color="NIVEL MÁS ALTO QUE CURSÓ",
              color_discrete_sequence=px.colors.qualitative.Safe)
fig1.update_layout(showlegend=False, height=420)
st.plotly_chart(fig1, use_container_width=True)
st.divider()

# ── GRÁFICO 2: Educación por departamento ─────────────────────────────────────
st.subheader("Nivel educativo por departamento")
g2 = (fil_edu[~fil_edu["NIVEL MÁS ALTO QUE CURSÓ"].isin(SIN_DATO)]
      .groupby(["DEPARTAMENTO", "NIVEL MÁS ALTO QUE CURSÓ"])["Personas"].sum()
      .reset_index())
fig2 = px.bar(g2, x="DEPARTAMENTO", y="Personas",
              color="NIVEL MÁS ALTO QUE CURSÓ", barmode="stack",
              labels={"DEPARTAMENTO": "Departamento", "NIVEL MÁS ALTO QUE CURSÓ": "Nivel educativo"},
              color_discrete_sequence=px.colors.qualitative.Safe)
fig2.update_layout(xaxis_tickangle=-45, height=480, legend_title="Nivel educativo")
st.plotly_chart(fig2, use_container_width=True)
st.divider()

# ── GRÁFICO 3: Educación por área ─────────────────────────────────────────────
st.subheader("Nivel educativo por área (Urbano / Rural)")
g3 = (fil_edu[~fil_edu["NIVEL MÁS ALTO QUE CURSÓ"].isin(SIN_DATO)]
      .groupby([area_col, "NIVEL MÁS ALTO QUE CURSÓ"])["Personas"].sum()
      .reset_index())
fig3 = px.bar(g3, x=area_col, y="Personas",
              color="NIVEL MÁS ALTO QUE CURSÓ", barmode="group",
              labels={area_col: "Área", "NIVEL MÁS ALTO QUE CURSÓ": "Nivel educativo"},
              color_discrete_sequence=px.colors.qualitative.Safe)
fig3.update_layout(height=420, legend_title="Nivel educativo")
st.plotly_chart(fig3, use_container_width=True)
st.divider()

# ── GRÁFICO 4: Educación por sexo (%) ─────────────────────────────────────────
st.subheader("Nivel educativo más alto cursado por sexo")
g4 = (fil_edu[
        ~fil_edu["NIVEL MÁS ALTO QUE CURSÓ"].isin(SIN_DATO) &
        fil_edu["SEXO AL NACER"].isin(["HOMBRE", "MUJER"])
      ].groupby(["SEXO AL NACER", "NIVEL MÁS ALTO QUE CURSÓ"])["Personas"].sum()
      .reset_index())
if len(g4) > 0:
    g4["Porcentaje"] = (
        g4["Personas"] / g4.groupby("SEXO AL NACER")["Personas"].transform("sum") * 100
    ).round(1)
    fig4 = px.bar(g4, x="NIVEL MÁS ALTO QUE CURSÓ", y="Porcentaje",
                  color="SEXO AL NACER", barmode="group",
                  labels={"NIVEL MÁS ALTO QUE CURSÓ": "Nivel educativo",
                          "Porcentaje": "% dentro del sexo", "SEXO AL NACER": "Sexo"},
                  color_discrete_map={"HOMBRE": "#3498db", "MUJER": "#e91e8c"})
    fig4.update_layout(xaxis_tickangle=-30, height=480)
    st.plotly_chart(fig4, use_container_width=True)
st.divider()

# ── GRÁFICO 5: Acceso a internet por departamento ─────────────────────────────
st.subheader("Acceso a internet por departamento")
g5 = (fil[fil["ACCESO A INTERNET"].isin(["Sí", "No"])]
      .groupby(["DEPARTAMENTO", "ACCESO A INTERNET"])["Personas"].sum()
      .reset_index())
fig5 = px.bar(g5, x="DEPARTAMENTO", y="Personas",
              color="ACCESO A INTERNET", barmode="group",
              labels={"DEPARTAMENTO": "Departamento", "ACCESO A INTERNET": "Internet"},
              color_discrete_map={"Sí": "#2ecc71", "No": "#e74c3c"})
fig5.update_layout(xaxis_tickangle=-45, height=420)
st.plotly_chart(fig5, use_container_width=True)
st.divider()

# ── MAPA ──────────────────────────────────────────────────────────────────────
st.subheader("Mapa — Nivel educativo por departamento y sexo")
nivel_mapa = st.selectbox("Seleccioná el nivel educativo", options=NIVELES_ORDEN)
g6 = (fil[
        (fil["NIVEL MÁS ALTO QUE CURSÓ"] == nivel_mapa) &
        fil["SEXO AL NACER"].isin(["HOMBRE", "MUJER"])
      ].groupby(["DEPARTAMENTO", "SEXO AL NACER"])["Personas"].sum()
      .reset_index())
g6["lat"] = g6["DEPARTAMENTO"].map(lambda d: COORDS.get(d, (None, None))[0])
g6["lon"] = g6["DEPARTAMENTO"].map(lambda d: COORDS.get(d, (None, None))[1])
g6["lat"] = g6.apply(
    lambda r: r["lat"] + (0.15 if r["SEXO AL NACER"] == "MUJER" else -0.15) if r["lat"] else None, axis=1)
g6 = g6.dropna(subset=["lat", "lon"])
fig6 = px.scatter_mapbox(
    g6, lat="lat", lon="lon", size="Personas", color="SEXO AL NACER",
    hover_name="DEPARTAMENTO",
    hover_data={"Personas": True, "SEXO AL NACER": True, "lat": False, "lon": False},
    color_discrete_map={"HOMBRE": "#3498db", "MUJER": "#e91e8c"},
    size_max=60, zoom=5.5,
    center={"lat": -32.5, "lon": -56.0},
    mapbox_style="carto-positron",
    title=f"Nivel: {nivel_mapa}"
)
fig6.update_layout(height=600, legend_title="Sexo")
st.plotly_chart(fig6, use_container_width=True)
st.divider()

with st.expander("Ver tabla agregada filtrada"):
    st.dataframe(fil.head(500), use_container_width=True)