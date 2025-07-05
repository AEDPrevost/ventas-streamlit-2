import streamlit as st
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Sistema de Ventas", layout="centered")
st.title("🛍️ Sistema de Ventas")
st.markdown("Registra ventas, gastos y donaciones directamente en Google Sheets.")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/194LULN6JNb-QR7GAvLEqS6ISCc1zL3HNQclhe-2DnqI/edit?usp=sharing"
spreadsheet = client.open_by_url(SHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

precios = {
    "PopCombo": 75,
    "HotCombo": 125,
    "FullCombo": 150,
    "HotDog": 50,
    "Palomitas": 100,
    "Refresco": 30
}

with st.form("formulario"):
    st.subheader("🧾 Selección de productos")
    cantidades = {producto: st.number_input(f"{producto} (RD${precio})", min_value=0, step=1, key=producto) for producto, precio in precios.items()}
    gastos_extra = st.number_input("💸 Gastos Extra (opcional)", min_value=0.0, step=10.0)
    donacion = st.number_input("🎁 Donación (opcional)", min_value=0.0, step=10.0)
    pago = st.number_input("💵 Monto pagado por el cliente", min_value=0.0, step=10.0)
    enviado = st.form_submit_button("📥 Registrar Venta")

if enviado:
    total_productos = sum(cantidades[p] * precios[p] for p in precios)
    if donacion > 0:
        total = donacion
        devuelta = 0
    elif gastos_extra > 0 and total_productos == 0:
        total = -gastos_extra
        devuelta = 0
    else:
        total = total_productos - gastos_extra
        devuelta = pago - total

    if total > 0 and pago < total:
        st.error(f"❌ El pago es insuficiente. Faltan RD${total - pago:.2f}")
    else:
        fila = {
            **cantidades,
            "GastosExtra": 1 if gastos_extra > 0 else 0,
            "Donacion": 1 if donacion > 0 else 0,
            "Total": total,
            "Pago": pago,
            "Devuelta": devuelta
        }
        existing = pd.DataFrame(worksheet.get_all_records())
        updated = pd.concat([existing, pd.DataFrame([fila])], ignore_index=True)
        worksheet.clear()
        set_with_dataframe(worksheet, updated)
        st.success("✅ Venta registrada correctamente.")
        st.metric("Total", f"RD${total:.2f}")
        st.metric("Devuelta", f"RD${devuelta:.2f}")
