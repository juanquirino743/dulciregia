import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Sistema Dulciregia v6",
    layout="wide",
    page_icon="🍭"
)

# ---------------- ESTILOS ----------------
st.markdown("""
<style>
.stButton>button {
    background-color:#FF0000;
    color:white;
    border-radius:8px;
    font-weight:bold;
    width:100%;
    height:3em;
}
.stMetric {
    background:#f0faff;
    padding:15px;
    border-radius:10px;
    border-left:5px solid #00AEEF;
}
</style>
""", unsafe_allow_html=True)

# ---------------- BASE DATOS ----------------
CAT_FILE = "catalogo_dulciregia.csv"
REG_FILE = "registros_movimientos.csv"

def get_catalog():
    if os.path.exists(CAT_FILE):
        df = pd.read_csv(CAT_FILE)
        df.columns = [c.strip() for c in df.columns]
        df.rename(columns={
            "Descripción":"Producto",
            "Descripcion":"Producto",
            "Nombre":"Producto"
        }, inplace=True)
        df["Clave"] = df["Clave"].astype(str)
        df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=["Clave","Producto","Precio"])

def get_records():
    if os.path.exists(REG_FILE):
        df = pd.read_csv(REG_FILE)
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=[
        "ID","Fecha","Colaborador","Producto",
        "Tipo","Cantidad","Precio_Unit",
        "Total","Observaciones"
    ])
def generar_pdf(df, titulo):

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica", 14)
    c.drawString(50, 750, titulo)

    y = 720
    c.setFont("Helvetica", 10)

    for index, row in df.iterrows():

        texto = f"{row['Fecha']} | {row['Producto']} | Cantidad: {row['Cantidad']} | Total: ${row['Total']}"
        c.drawString(50, y, texto)

        y -= 20

        if y < 50:
            c.showPage()
            y = 750

    c.save()
    buffer.seek(0)

    return buffer

# ---------------- MENU ----------------
menu = [
    "📊 Dashboard",
    "📝 Nuevo Registro",
    "⚙️ Gestionar Registros",
    "📦 Catálogo (Ver/Editar)",
    "📂 Carga/Pegado Masivo"
]

choice = st.sidebar.radio("Menú Principal", menu)

# =========================================================
# NUEVO REGISTRO
# =========================================================
if choice == "📝 Nuevo Registro":

    st.title("📝 Registro de Movimiento")
    cat = get_catalog()

    if cat.empty:
        st.warning("Catálogo vacío.")
    else:

        cat["Busqueda"] = cat["Clave"] + " | " + cat["Producto"]

        with st.form("form_registro", clear_on_submit=True):

            col1, col2 = st.columns(2)

            with col1:
                fecha = st.date_input("Fecha", datetime.now())
                colaborador = st.text_input("Colaborador")
                seleccion = st.selectbox(
                    "Producto",
                    cat["Busqueda"]
                )

            with col2:
                tipo = st.selectbox(
                    "Tipo",
                    ["Uso de Insumo","Merma"]
                )
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    step=1
                )
                obs = st.text_area("Observaciones")

            guardar = st.form_submit_button("💾 Guardar")

            if guardar:

                if colaborador and seleccion:

                    producto = seleccion.split(" | ")[1]
                    precio = cat[
                        cat["Producto"] == producto
                    ]["Precio"].values[0]

                    hist = get_records()
                    nuevo_id = (
                        int(hist["ID"].max()) + 1
                        if not hist.empty else 1
                    )

                    nuevo = pd.DataFrame([{
                        "ID":nuevo_id,
                        "Fecha":fecha,
                        "Colaborador":colaborador,
                        "Producto":producto,
                        "Tipo":tipo,
                        "Cantidad":cantidad,
                        "Precio_Unit":precio,
                        "Total":precio * cantidad,
                        "Observaciones":obs
                    }])

                    pd.concat([hist,nuevo]) \
                      .to_csv(REG_FILE,index=False)

                    st.success("Registro guardado")
                    st.rerun()

                else:
                    st.error("Faltan datos")

# =========================================================
# DASHBOARD
# =========================================================
elif choice == "📊 Dashboard":

    st.title("📊 Dashboard")

    df = get_records()

    if df.empty:
        st.info("Sin registros")
    else:

        merma = df[df["Tipo"]=="Merma"]

        total_merma = float(merma["Total"].sum())
        piezas_merma = int(merma["Cantidad"].sum())

        c1,c2 = st.columns(2)

        c1.metric(
            "Pérdida Total Merma",
            f"${total_merma:,.2f}"
        )

        c2.metric(
            "Piezas Perdidas",
            f"{piezas_merma:,}"
        )

        top = (
            merma.groupby("Producto")["Cantidad"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            top,
            x="Cantidad",
            y="Producto",
            orientation="h",
            title="Top 10 Productos con más Merma"
        )

        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# GESTIONAR
# =========================================================
elif choice == "⚙️ Gestionar Registros":

    st.title("⚙️ Gestionar")

    df = get_records()

    if df.empty:
        st.info("Sin datos")
    else:
        st.dataframe(df, use_container_width=True)

        borrar = st.number_input(
            "ID a eliminar",
            min_value=1,
            step=1
        )

        if st.button("Eliminar"):
            df = df[df["ID"] != borrar]
            df.to_csv(REG_FILE,index=False)
            st.success("Eliminado")
            st.rerun()

# =========================================================
# CATALOGO
# =========================================================
elif choice == "📦 Catálogo (Ver/Editar)":

    st.title("📦 Catálogo")

    df = get_catalog()

    edit = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("Guardar Cambios"):
        edit.to_csv(CAT_FILE,index=False)
        st.success("Guardado")
        st.rerun()

# =========================================================
# CARGA MASIVA
# =========================================================
elif choice == "📂 Carga/Pegado Masivo":

    st.title("📂 Carga Masiva")

    txt = st.text_area(
        "Pega desde Excel",
        height=200
    )

    if st.button("Procesar"):

        if txt:

            df = pd.read_csv(
                io.StringIO(txt),
                sep="\t",
                header=None,
                names=["Clave","Producto","Precio"]
            )

            df.to_csv(CAT_FILE,index=False)

            st.success("Catálogo cargado")

