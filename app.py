import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from dotenv import load_dotenv
import os

# --- Configuração Inicial --- #
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

# Configuração da página
st.set_page_config(
    page_title="Previsão do Tempo em Portugal",
    page_icon="🌤️",
    layout="centered"
)

# --- Constantes --- #
CIDADES_PORTUGAL = {
    "Montijo": {"lat": 38.70, "lon": -8.97},
    "Lisboa": {"lat": 38.72, "lon": -9.14},
    "Porto": {"lat": 41.15, "lon": -8.61},
    "Braga": {"lat": 41.55, "lon": -8.42},
    "Coimbra": {"lat": 40.21, "lon": -8.42},
    "Faro": {"lat": 37.02, "lon": -7.93},
    "Aveiro": {"lat": 40.64, "lon": -8.65},
    "Évora": {"lat": 38.57, "lon": -7.91},
    "Setúbal": {"lat": 38.52, "lon": -8.89},
    "Viseu": {"lat": 40.664, "lon": -7.916}
}
# Previsão para os próximos dias
DIAS_SEMANA = {
    "Monday": "Seg",
    "Tuesday": "Ter",
    "Wednesday": "Qua",
    "Thursday": "Qui",
    "Friday": "Sex",
    "Saturday": "Sáb",
    "Sunday": "Dom"
}

API_ENDPOINTS = {
    "current": "https://api.weatherapi.com/v1/current.json",
    "forecast": "https://api.weatherapi.com/v1/forecast.json"
}

# --- Gestão de Secrets --- #
def get_api_key():
    """Obtém a API Key na ordem de prioridade correta"""
    try:
        # 1. Tenta via secrets.toml (Streamlit)
        if "WEATHER" in st.secrets and "API_KEY" in st.secrets["WEATHER"]:
            return st.secrets["WEATHER"]["API_KEY"]
        
        # 2. Tenta via variável de ambiente
        if "WEATHER_API_KEY" in os.environ:
            return os.environ["WEATHER_API_KEY"]
            
    except Exception as e:
        st.warning(f"Aviso na leitura de secrets: {str(e)}")
    
    return None

api_key = get_api_key()

if not api_key:
    st.error("""
    🔐 Configuração de API Key necessária:
    
    **Opção 1 (Recomendada para local):**  
    Crie `.streamlit/secrets.toml` com:
    ```toml
    [WEATHER]
    API_KEY = "sua_chave_aqui"
    ```
    
    **Opção 2 (Para produção):**  
    Defina a variável de ambiente `WEATHER_API_KEY`
    """)
    st.stop()

# --- Interface do Usuário --- #
st.title("🌤️ Previsão do Tempo - Portugal")

# Sidebar com seletor de cidade
with st.sidebar:
    st.header("Configurações")
    cidade_selecionada = st.selectbox(
        "Selecione uma cidade:",
        options=list(CIDADES_PORTUGAL.keys()),
        index=0
    )
    st.write(f"Coordenadas: {CIDADES_PORTUGAL[cidade_selecionada]['lat']}, {CIDADES_PORTUGAL[cidade_selecionada]['lon']}")
    dias_previsao = st.slider("Dias de previsão", 1, 3, 2)

# --- Lógica de Obtenção de Dados --- #
@st.cache_data(ttl=3600)  # Cache por 1 hora
def fetch_weather_data(endpoint, params):
    """Função para buscar dados da API com cache"""
    response = requests.get(endpoint, params=params)
    response.raise_for_status()  # Levanta exceção para erros HTTP
    return response.json()

# Obter dados meteorológicos
try:
    coord = CIDADES_PORTUGAL[cidade_selecionada]
    q_param = f"{coord['lat']},{coord['lon']}"
    
    with st.spinner(f'Obtendo dados para {cidade_selecionada}...'):
        # Dados atuais
        dados_current = fetch_weather_data(
            API_ENDPOINTS["current"],
            {
                "key": api_key,
                "q": q_param,
                "lang": "pt"
            }
        )
        
        # Dados de previsão
        dados_forecast = fetch_weather_data(
            API_ENDPOINTS["forecast"],
            {
                "key": api_key,
                "q": q_param,
                "lang": "pt",
                "days": dias_previsao
            }
        )
        
    current = dados_current["current"]
    location = dados_current["location"]
    
    # --- Exibição dos Resultados --- #
    
    # Layout principal - Condições atuais
    st.header(f"Condições atuais em {cidade_selecionada}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperatura", f"{current['temp_c']}°C")
        st.metric("Sensação Térmica", f"{current['feelslike_c']}°C")
    with col2:
        st.write(f"**Condição:** {current['condition']['text']}")
        st.image(f"https:{current['condition']['icon']}", width=100)
    with col3:
        st.metric("Humidade", f"{current['humidity']}%")
        st.metric("Vento", f"{current['wind_kph']} km/h")
    
    # Mapa Folium
    with st.expander("🗺️ Ver no mapa (interativo)"):
        try:
            m = folium.Map(
                location=[float(location['lat']), float(location['lon'])],
                zoom_start=12,
                tiles="OpenStreetMap"
            )
            
            folium.Marker(
                [float(location['lat']), float(location['lon'])],
                popup=f"{cidade_selecionada}<br>Temperatura: {current['temp_c']}°C",
                tooltip="Clique para detalhes",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)
            
            st_folium(m, width=700, height=500, returned_objects=[])
            
        except Exception as e:
            st.error(f"Erro ao gerar mapa: {str(e)}")

    # Detalhes adicionais
    with st.expander("🔍 Detalhes completos"):
        st.subheader("Informações Meteorológicas")
        st.write(f"**Coordenadas:** {location['lat']}, {location['lon']}")
        st.write(f"**Última atualização:** {current['last_updated']}")
        st.write(f"**Pressão atmosférica:** {current['pressure_mb']} mb")
        st.write(f"**Índice UV:** {current['uv']}")
        st.write(f"**Visibilidade:** {current['vis_km']} km")
        
        if st.checkbox("Mostrar dados brutos da API (atual)"):
            st.json(dados_current)
    
    # Previsão para os próximos dias
    st.header(f"⏳ Previsão para os próximos {dias_previsao} dias em {cidade_selecionada}")
    
    forecast_days = dados_forecast["forecast"]["forecastday"]
    
    for day in forecast_days:
        date = datetime.strptime(day["date"], "%Y-%m-%d")
        weekday_pt = DIAS_SEMANA[date.strftime("%A")]
        data_pt = date.strftime("%d/%m")
        
        with st.expander(f"{weekday_pt}, {data_pt}"):  # Ex: "Sáb, 10/05"
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("🌡️ Temperatura")
                st.write(f"**Máxima:** {day['day']['maxtemp_c']}°C")
                st.write(f"**Mínima:** {day['day']['mintemp_c']}°C")
                st.write(f"**Média:** {day['day']['avgtemp_c']}°C")
            
            with col2:
                st.subheader("🌦️ Condições")
                st.image(f"https:{day['day']['condition']['icon']}", width=70)
                st.write(day['day']['condition']['text'])
                st.write(f"**Chuva:** {day['day']['totalprecip_mm']} mm")
                st.write(f"**UV:** {day['day']['uv']}")
            
            with col3:
                st.subheader("💨 Vento & Outros")
                st.write(f"**Vel. vento:** {day['day']['maxwind_kph']} km/h")
                st.write(f"**Humidade:** {day['day']['avghumidity']}%")
                st.write(f"**Visibilidade:** {day['day']['avgvis_km']} km")
            
            # Previsão horária (simplificada)
            st.subheader("🕒 Previsão horária")
            horas = day["hour"]
            horas_selecionadas = [horas[0], horas[6], horas[12], horas[18]]
            
            for hora in horas_selecionadas:
                time = hora["time"].split()[1]
                col1, col2, col3, col4 = st.columns([1,1,2,1])
                with col1:
                    st.write(f"**{time}**")
                with col2:
                    st.write(f"{hora['temp_c']}°C")
                with col3:
                    st.image(f"https:{hora['condition']['icon']}", width=30)
                    st.write(hora['condition']['text'])
                with col4:
                    st.write(f"💧 {hora['humidity']}%")
            
            if st.checkbox(f"Mostrar todas as horas para {day['date']}"):
                df_horas = pd.DataFrame(day["hour"])
                df_horas = df_horas[["time", "temp_c", "condition", "humidity", "wind_kph"]]
                df_horas["condition_text"] = df_horas["condition"].apply(lambda x: x["text"])
                df_horas["condition_icon"] = df_horas["condition"].apply(lambda x: f"https:{x['icon']}")
                st.dataframe(df_horas.drop(columns=["condition"]))
    
    if st.checkbox("Mostrar dados brutos da API (previsão)"):
        st.json(dados_forecast)

except requests.exceptions.RequestException as e:
    st.error(f"Erro na conexão com a API: {str(e)}")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {str(e)}")

# Rodapé
st.divider()
st.caption("© 2025 Mario/Mythus | 🌦️ Fonte: [WeatherAPI](https://www.weatherapi.com/)")