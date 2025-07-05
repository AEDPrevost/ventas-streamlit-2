
import streamlit as st
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# CONFIG
st.set_page_config(page_title="Sistema de Ventas", layout="centered")
st.title("🛍️ Sistema de Ventas")
st.markdown("Registra ventas, gastos y donaciones directamente en Google Sheets.")

# AUTENTICACIÓN
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
SHEET_URL = "https://docs.google.com/spreadsheets/d/194LULN6JNb-QR7GAvLEqS6ISCc1zL3HNQclhe-2DnqI/edit?usp=sharing"
spreadsheet = client.open_by_url(SHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# PRECIOS
precios = {
    "PopCombo": 75,
    "HotCombo": 125,
    "FullCombo": 150,
    "HotDog": 50,
    "Palomitas": 100,
    "Refresco": 30
}

# ESTADO DE SESIÓN
if "total" not in st.session_state:
    st.session_state.total = 0
if "calculado" not in st.session_state:
    st.session_state.calculado = False
if "pagado" not in st.session_state:
    st.session_state.pagado = 0
if "devuelta" not in st.session_state:
    st.session_state.devuelta = 0
if "venta_registrada" not in st.session_state:
    st.session_state.venta_registrada = False

st.subheader("🧾 Selección de productos")
cantidades = {}
for producto, precio in precios.items():
    cantidades[producto] = st.number_input(f"{producto} (RD${precio})", min_value=0, step=1, key=producto)

gastos_extra = st.number_input("💸 Gastos Extra (opcional)", min_value=0.0, step=10.0)
donacion = st.number_input("🎁 Donación (opcional)", min_value=0.0, step=10.0)

if st.button("🔢 Calcular Total"):
    total_productos = sum(cantidades[p] * precios[p] for p in precios)
    if donacion > 0:
        st.session_state.total = donacion
    elif gastos_extra > 0 and total_productos == 0:
        st.session_state.total = -gastos_extra
    else:
        st.session_state.total = total_productos - gastos_extra
    st.session_state.calculado = True
    st.session_state.venta_registrada = False

if st.session_state.calculado:
    st.success(f"💰 Total a pagar: RD${st.session_state.total:.2f}")
    st.session_state.pagado = st.number_input("💵 Monto pagado por el cliente", min_value=0.0, step=10.0, key="pago_cliente")

    if st.button("💸 Calcular Devuelta"):
        if st.session_state.total > 0 and st.session_state.pagado < st.session_state.total:
            st.error(f"❌ El pago es insuficiente. Faltan RD${st.session_state.total - st.session_state.pagado:.2f}")
        else:
            st.session_state.devuelta = st.session_state.pagado - st.session_state.total
            st.success(f"🪙 Devuelta: RD${st.session_state.devuelta:.2f}")

if st.session_state.devuelta >= 0 and st.session_state.calculado:
    if st.button("📥 Registrar Venta"):
        fila = {
            **cantidades,
            "GastosExtra": 1 if gastos_extra > 0 else 0,
            "Donacion": 1 if donacion > 0 else 0,
            "Total": st.session_state.total,
            "Pago": st.session_state.pagado,
            "Devuelta": st.session_state.devuelta
        }
        existing = pd.DataFrame(worksheet.get_all_records())
        updated = pd.concat([existing, pd.DataFrame([fila])], ignore_index=True)
        worksheet.clear()
        set_with_dataframe(worksheet, updated)
        st.success("✅ Venta registrada correctamente.")
        st.session_state.venta_registrada = True
        st.experimental_rerun()

# ESTADÍSTICAS
st.markdown("---")
if st.button("📊 Ver estadísticas"):
    data = pd.DataFrame(worksheet.get_all_records())
    if not data.empty:
        totales = data[["PopCombo", "HotCombo", "FullCombo", "HotDog", "Palomitas", "Refresco"]].sum()
        total_ganado = data["Total"].sum()
        total_donaciones = data[data["Donacion"] == 1]["Total"].sum()
        total_gastos = -data[data["GastosExtra"] == 1]["Total"].sum()
        st.subheader("📈 Estadísticas actuales")
        st.write("🧾 Cantidad vendida por producto:")
        st.write(totales.astype(int))
        st.metric("💵 Total acumulado", f"RD${total_ganado:.2f}")
        st.metric("🎁 Total donaciones", f"RD${total_donaciones:.2f}")
        st.metric("💸 Total en gastos", f"RD${total_gastos:.2f}")
    else:
        st.info("Aún no hay ventas registradas.")
