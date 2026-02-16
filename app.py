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
    page_title="Sistema Dulciregia v8",
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
</style>
""", unsafe_allow_html=True)

# ---------------- ARCHIVOS ----------------
CAT_FILE = "catalogo_dulciregia.csv"
REG_FILE = "registros_movimientos.csv"

# ---------------- CATALOGO ----------------
def get_catalog():

    if os.path.exists(CAT_FILE):

        df = pd.read_csv(CAT_FILE)

        df["Clave"] = df["Clave"].astype(str)

        df["Precio"] = pd.to_numeric(
            df["Precio"],
            errors="coerce"
        ).fillna(0)

        return df

    return pd.DataFrame(
        columns=["Clave","Producto","Precio"]
    )

# ---------------- REGISTROS ----------------
def get_records():

    if os.path.exists(REG_FILE):

        df = pd.read_csv(REG_FILE)

        df["Cantidad"] = pd.to_numeric(
            df["Cantidad"],
            errors="coerce"
        ).fillna(0)

        df["Precio_Unit"] = pd.to_numeric(
            df["Precio_Unit"],
            errors="coerce"
        ).fillna(0)

        df["Total"] = df["Cantidad"] * df["Precio_Unit"]

        return df

    return pd.DataFrame(columns=[
        "ID",
        "Fecha",
        "Colaborador",
        "Producto",
        "Tipo",
        "Unidad",
        "Cantidad",
        "Precio_Unit",
        "Total",
        "Observaciones"
    ])

# ---------------- PDF ----------------
def generar_pdf(df, titulo):

    buffer = io.BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=letter
    )

    c.setFont("Helvetica",14)
    c.drawString(50,750,titulo)

    y=720

    for _, row in df.iterrows():

        texto = (
            f"{row['Fecha']} | "
            f"{row['Producto']} | "
            f"{row['Cantidad']} {row['Unidad']} | "
            f"${row['Total']:.2f}"
        )

        c.drawString(50,y,texto)

        y -= 20

        if y < 50:
            c.showPage()
            y=750

    c.save()

    buffer.seek(0)

    return buffer

# ---------------- MENU ----------------
menu = [
    "📊 Dashboard",
    "📝 Nuevo Registro",
    "⚙️ Gestionar Registros",
    "📦 Catálogo",
    "📂 Carga Masiva"
]

choice = st.sidebar.radio(
    "Menú Principal",
    menu
)

# =====================================================
# NUEVO REGISTRO
# =====================================================
if choice == "📝 Nuevo Registro":

    st.title("Nuevo Registro")

    cat = get_catalog()

    if cat.empty:

        st.warning("Catálogo vacío")

    else:

        cat["Busqueda"] = (
            cat["Clave"]
            + " | "
            + cat["Producto"]
        )

        with st.form("form"):

            fecha = st.date_input(
                "Fecha",
                datetime.now()
            )

            colaborador = st.text_input(
                "Colaborador"
            )

            seleccion = st.selectbox(
                "Producto",
                cat["Busqueda"]
            )

            tipo = st.selectbox(
                "Tipo",
                ["Uso de Insumo","Merma"]
            )

            unidad = st.selectbox(
                "Unidad",
                ["Pieza","Kilogramo"]
            )

            cantidad = st.number_input(
                "Cantidad",
                min_value=0.01,
                step=0.01
            )

            obs = st.text_input(
                "Observaciones"
            )

            guardar = st.form_submit_button(
                "Guardar"
            )

            if guardar:

                producto = seleccion.split(" | ")[1]

                precio = cat[
                    cat["Producto"] == producto
                ]["Precio"].values[0]

                total = cantidad * precio

                df = get_records()

                nuevo_id = (
                    df["ID"].max()+1
                    if not df.empty
                    else 1
                )

                nuevo = pd.DataFrame([{
                    "ID":nuevo_id,
                    "Fecha":fecha,
                    "Colaborador":colaborador,
                    "Producto":producto,
                    "Tipo":tipo,
                    "Unidad":unidad,
                    "Cantidad":cantidad,
                    "Precio_Unit":precio,
                    "Total":total,
                    "Observaciones":obs
                }])

                df = pd.concat([df,nuevo])

                df.to_csv(
                    REG_FILE,
                    index=False
                )

                st.success("Guardado")

# =====================================================
# DASHBOARD
# =====================================================
elif choice == "📊 Dashboard":

    st.title("Dashboard")

    df = get_records()

    if df.empty:

        st.info("Sin datos")

    else:

        merma = df[df["Tipo"]=="Merma"]

        insumo = df[df["Tipo"]=="Uso de Insumo"]

        c1,c2,c3,c4 = st.columns(4)

        c1.metric(
            "Dinero Merma",
            f"${merma['Total'].sum():.2f}"
        )

        c2.metric(
            "Cantidad Merma",
            f"{merma['Cantidad'].sum():.2f}"
        )

        c3.metric(
            "Dinero Insumos",
            f"${insumo['Total'].sum():.2f}"
        )

        c4.metric(
            "Cantidad Insumos",
            f"{insumo['Cantidad'].sum():.2f}"
        )

        pdf_merma = generar_pdf(
            merma,
            "Reporte Merma"
        )

        st.download_button(
            "Descargar PDF Merma",
            pdf_merma,
            "merma.pdf"
        )

        pdf_insumo = generar_pdf(
            insumo,
            "Reporte Insumos"
        )

        st.download_button(
            "Descargar PDF Insumos",
            pdf_insumo,
            "insumos.pdf"
        )

# =====================================================
# GESTIONAR
# =====================================================
elif choice == "⚙️ Gestionar Registros":

    st.title("Registros")

    df = get_records()

    st.dataframe(df)

# =====================================================
# CATALOGO
# =====================================================
elif choice == "📦 Catálogo":

    st.title("Catalogo")

    df = get_catalog()

    edit = st.data_editor(df)

    if st.button("Guardar"):

        edit.to_csv(
            CAT_FILE,
            index=False
        )

# =====================================================
# CARGA MASIVA
# =====================================================
elif choice == "📂 Carga Masiva":

    st.title("Carga Masiva")

    txt = st.text_area("Pegar Excel")

    if st.button("Procesar"):

        if txt:

            nuevo = pd.read_csv(
                io.StringIO(txt),
                sep="\t",
                header=None,
                names=[
                    "Clave",
                    "Producto",
                    "Precio"
                ]
            )

            if os.path.exists(CAT_FILE):

                existente = pd.read_csv(CAT_FILE)

                final = pd.concat([
                    existente,
                    nuevo
                ]).drop_duplicates(
                    subset="Clave",
                    keep="last"
                )

            else:

                final = nuevo

            final.to_csv(
                CAT_FILE,
                index=False
            )

            st.success("Actualizado")
