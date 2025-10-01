from fastapi import FastAPI, Response
from pymongo import MongoClient
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

app = FastAPI()

# URI de conexión a Mongo Atlas (se pasa por variable de entorno en OpenShift)
MONGO_URI = os.getenv("MONGO_URI", "")
client = MongoClient(MONGO_URI)
db = client["compraalquilerbicicletas"]
collection = db["comprayalquiler"]

@app.get("/reporte")
def generar_reporte():
    docs = list(collection.find())
    if not docs:
        return {"error": "No hay datos en la base de datos"}

    df = pd.DataFrame(docs)

    # Calcular ingresos
    df["ingreso"] = df.apply(
        lambda row: row["price"] * row["period"]
        if row["mode"] == "alquiler"
        else row["price"],
        axis=1,
    )

    ingresos_compra = df[df["mode"] == "compra"]["ingreso"].sum()
    ingresos_alquiler = df[df["mode"] == "alquiler"]["ingreso"].sum()

    # Convertir fechas
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    else:
        df["created_at"] = [datetime.utcnow().replace(tzinfo=timezone.utc)] * len(df)

    timeline = (
        df.groupby([pd.Grouper(key="created_at", freq="D"), "mode"])["ingreso"]
        .sum()
        .unstack(fill_value=0)
    )

    # --- Gráficas ---
    figs = []

    # 1. Línea de tiempo
    fig1, ax1 = plt.subplots()
    timeline.plot(ax=ax1)
    ax1.set_title("Ingresos diarios por modo")
    buf1 = BytesIO()
    plt.savefig(buf1, format="png")
    buf1.seek(0)
    figs.append(buf1)

    # 2. Pastel Compra vs Alquiler
    fig2, ax2 = plt.subplots()
    df["mode"].value_counts().plot.pie(ax=ax2, autopct="%1.1f%%")
    ax2.set_ylabel("")
    ax2.set_title("Distribución Compra vs Alquiler")
    buf2 = BytesIO()
    plt.savefig(buf2, format="png")
    buf2.seek(0)
    figs.append(buf2)

    # 3. Pastel Tipos de bicicletas
    if "type" in df.columns:
        fig3, ax3 = plt.subplots()
        df["type"].value_counts().plot.pie(ax=ax3, autopct="%1.1f%%")
        ax3.set_ylabel("")
        ax3.set_title("Tipos de bicicletas")
        buf3 = BytesIO()
        plt.savefig(buf3, format="png")
        buf3.seek(0)
        figs.append(buf3)

    # --- PDF ---
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Reporte Bicicletas", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            f"Fecha de generación: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Total ingresos (compra): {ingresos_compra}", styles["Normal"]))
    story.append(Paragraph(f"Total ingresos (alquiler): {ingresos_alquiler}", styles["Normal"]))
    story.append(Spacer(1, 20))

    for fig in figs:
        story.append(Image(fig, width=400, height=300))
        story.append(Spacer(1, 20))

    doc.build(story)
    pdf_buf.seek(0)

    return Response(pdf_buf.read(), media_type="application/pdf")



