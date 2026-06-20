import streamlit as st
import pandas as pd
import hmac
import json
import base64
from datetime import date
from streamlit_gsheets import GSheetsConnection
from groq import Groq
URL_EXCEL=st.secrets["url"]
st.set_page_config(page_title="Pastelería",layout="centered")
st.markdown("""<style>[data-testid="stSidebarCollapseButton"]{display:none !important;}[data-testid="collapsedSidebarHeader"]{display:none !important;}.stApp{background-color:#FAF8F5 !important;}[data-testid="stSidebar"]{background-color:#FFFFFF !important;border-right:3px solid #EFEBE9;}h1,h2,h3,h4,.stSubheader,.stMarkdown p,.stMarkdown li{color:#4E342E !important;font-family:'Quicksand','Segoe UI',sans-serif !important;}[data-testid="stWidgetLabel"] p{color:#4E342E !important;font-weight:700;}div[data-baseweb="input"],div[data-baseweb="select"],div[data-baseweb="popover"]{background-color:#FFFFFF !important;border-radius:20px !important;border:2px solid #D7CCC8 !important;transition:all 0.3s cubic-bezier(0.25,0.8,0.25,1) !important;}div[data-baseweb="input"]:focus-within,div[data-baseweb="select"]:focus-within{border-color:#8D6E63 !important;box-shadow:0 0 15px rgba(141,110,99,0.2) !important;transform:scale(1.02);}input{color:#4E342E !important;}.stButton>button{background-color:#FFFFFF !important;color:#4E342E !important;border-radius:25px !important;border:3px solid #8D6E63 !important;transition:all 0.3s cubic-bezier(0.25,0.8,0.25,1) !important;font-weight:bold !important;box-shadow:0 4px 6px rgba(0,0,0,0.05) !important;}.stButton>button:hover{transform:translateY(-5px) scale(1.03) !important;background-color:#8D6E63 !important;color:#FFFFFF !important;box-shadow:0 10px 20px rgba(141,110,99,0.3) !important;}.stButton>button:active{transform:translateY(2px) scale(0.95) !important;box-shadow:0 2px 4px rgba(0,0,0,0.1) !important;}div[data-testid="stDataFrame"]{background-color:#FFFFFF !important;border-radius:20px !important;padding:15px !important;border:2px solid #D7CCC8 !important;box-shadow:0 6px 12px rgba(0,0,0,0.05) !important;}</style>""",unsafe_allow_html=True)
def verificar_login():
    def comprobar():
        u=st.session_state["u_entry"]
        p=st.session_state["p_entry"]
        if u in st.secrets["usuarios"] and hmac.compare_digest(p,st.secrets["usuarios"][u]):
            st.session_state["autenticado"]=True
            del st.session_state["p_entry"]
            del st.session_state["u_entry"]
        else:
            st.session_state["autenticado"]=False
    if st.session_state.get("autenticado",False): return True
    st.title("Acceso Privado")
    st.text_input("Usuario",key="u_entry")
    st.text_input("Contraseña",type="password",key="p_entry")
    st.button("Ingresar al Sistema",on_click=comprobar)
    if "autenticado" in st.session_state and not st.session_state["autenticado"]: st.error("Credenciales incorrectas.")
    return False
if not verificar_login(): st.stop()
def normalizar_unidad(u):
    u=str(u).lower().strip()
    if u in ['l','lt','litro','litros']: return 'L'
    if u in ['ml','cc','mililitros']: return 'ml'
    if u in ['gr','g','gramo','gramos']: return 'gr'
    if u in ['kg','k','kilo','kilos']: return 'kg'
    if u in ['un','u','unidad','unidades','und','c/u']: return 'unidades'
    if u in ['paquete','pqte','paq']: return 'paquete'
    return "unidades"
hoy=str(date.today())
conn=st.connection("gsheets",type=GSheetsConnection)
try:
    df_insumos_raw=conn.read(spreadsheet=URL_EXCEL,worksheet="Insumos",ttl=600).dropna(how="all")
    if "Marca" not in df_insumos_raw.columns: df_insumos_raw["Marca"]="Genérico"
    if "Stock_Actual" not in df_insumos_raw.columns: df_insumos_raw["Stock_Actual"]=df_insumos_raw["Cantidad_Compra"]
    if "Última_Compra" not in df_insumos_raw.columns: df_insumos_raw["Última_Compra"]=hoy
    inventario=df_insumos_raw.to_dict(orient="records")
except Exception as e:
    st.error(f"Error en Insumos: {e}")
    inventario=[]
df_inv=pd.DataFrame(inventario)
try:
    df_recetas_raw=conn.read(spreadsheet=URL_EXCEL,worksheet="Recetas",ttl=600).dropna(how="all")
except Exception as e:
    st.error(f"Error en Recetas: {e}")
    df_recetas_raw=pd.DataFrame()
recetas={}
if not df_recetas_raw.empty:
    for _,fila in df_recetas_raw.iterrows():
        r_name=fila["Nombre_Receta"]
        if r_name not in recetas:
            r_cant=float(fila["Rendimiento_Cantidad"]) if "Rendimiento_Cantidad" in fila.index and pd.notnull(fila["Rendimiento_Cantidad"]) else (int(fila["Porciones"]) if "Porciones" in fila.index and pd.notnull(fila["Porciones"]) else 1.0)
            r_uni=fila["Rendimiento_Unidad"] if "Rendimiento_Unidad" in fila.index and pd.notnull(fila["Rendimiento_Unidad"]) else "porciones"
            recetas[r_name]={"rendimiento_cantidad":r_cant,"rendimiento_unidad":r_uni,"cif":float(fila["CIF"]) if pd.notnull(fila["CIF"]) else 0.0,"ingredientes":{}}
        if pd.notnull(fila["Insumo"]) and fila["Insumo"]!="":
            recetas[r_name]["ingredientes"][fila["Insumo"]]={"cantidad":float(fila["Cantidad"]),"unidad":fila["Unidad"]}
try:
    df_ventas_raw=conn.read(spreadsheet=URL_EXCEL,worksheet="Ventas",ttl=600).dropna(how="all")
    for col in ["ID Venta","Método de Pago","Estado","Observaciones"]:
        if col not in df_ventas_raw.columns: df_ventas_raw[col]=""
    ventas=df_ventas_raw.to_dict(orient="records")
except Exception as e:
    st.error(f"Error en Ventas: {e}")
    ventas=[]
def actualizar_insumos_cloud(nuevo_inv):
    conn.update(spreadsheet=URL_EXCEL,worksheet="Insumos",data=pd.DataFrame(nuevo_inv))
    st.cache_data.clear()
def actualizar_recetas_cloud(nuevas_rec):
    filas=[]
    for r_name,r_info in nuevas_rec.items():
        if not r_info["ingredientes"]:
            filas.append({"Nombre_Receta":r_name,"Rendimiento_Cantidad":r_info["rendimiento_cantidad"],"Rendimiento_Unidad":r_info["rendimiento_unidad"],"CIF":r_info["cif"],"Insumo":"","Cantidad":0,"Unidad":""})
        for ing_name,ing_data in r_info["ingredientes"].items():
            filas.append({"Nombre_Receta":r_name,"Rendimiento_Cantidad":r_info["rendimiento_cantidad"],"Rendimiento_Unidad":r_info["rendimiento_unidad"],"CIF":r_info["cif"],"Insumo":ing_name,"Cantidad":ing_data["cantidad"],"Unidad":ing_data["unidad"]})
    conn.update(spreadsheet=URL_EXCEL,worksheet="Recetas",data=pd.DataFrame(filas))
    st.cache_data.clear()
def actualizar_ventas_cloud(nuevas_ven):
    conn.update(spreadsheet=URL_EXCEL,worksheet="Ventas",data=pd.DataFrame(nuevas_ven))
    st.cache_data.clear()
def calcular_costo_insumo(insumo_obj,cant_receta,unidad_receta):
    c_uni=insumo_obj['Costo_Unitario']
    uni_inv=insumo_obj['Unidad']
    if uni_inv=="kg" and unidad_receta=="gr": return c_uni*(cant_receta/1000)
    if uni_inv=="gr" and unidad_receta=="kg": return c_uni*(cant_receta*1000)
    if uni_inv=="L" and unidad_receta=="ml": return c_uni*(cant_receta/1000)
    if uni_inv=="ml" and unidad_receta=="L": return c_uni*(cant_receta*1000)
    return c_uni*cant_receta
def obtener_costos_totales(r_name):
    if r_name not in recetas: return 0,0
    r_data=recetas[r_name]
    costo_directo=0
    if df_inv.empty: return 0,0
    for insumo_completo,datos_ing in r_data['ingredientes'].items():
        nombre_base=insumo_completo.split(" (")[0] if " (" in insumo_completo else insumo_completo
        filas_coincidentes=df_inv[df_inv['Nombre']==nombre_base]
        if not filas_coincidentes.empty:
            insumo_obj=filas_coincidentes.iloc[-1].to_dict()
            costo_directo+=calcular_costo_insumo(insumo_obj,datos_ing['cantidad'],datos_ing['unidad'])
    total=costo_directo+r_data['cif']
    costo_unitario_rendimiento=total/r_data['rendimiento_cantidad'] if r_data['rendimiento_cantidad']>0 else total
    return total,costo_unitario_rendimiento
st.sidebar.button("Cerrar Sesión",on_click=lambda:st.session_state.pop("autenticado",None))
menu=st.sidebar.radio("Navegación",["Inicio","Insumos","Fichas Técnicas","Rentabilidad","Ventas y Caja"])
if menu=="Inicio":
    st.header("Panel de Control")
    if ventas:
        df_v=pd.DataFrame(ventas)
        df_v["Total Cobrado ($)"]=pd.to_numeric(df_v["Total Cobrado ($)"],errors='coerce').fillna(0)
        df_v["Ganancia Neta ($)"]=pd.to_numeric(df_v["Ganancia Neta ($)"],errors='coerce').fillna(0)
        cobrado_real=df_v[df_v["Estado"]=="Pagado"]["Total Cobrado ($)"].sum()
        pendiente_cobro=df_v[df_v["Estado"]=="Pendiente"]["Total Cobrado ($)"].sum()
        ganancia_real=df_v[df_v["Estado"]=="Pagado"]["Ganancia Neta ($)"].sum()
        efectivo_total=df_v[(df_v["Método de Pago"]=="Efectivo")&(df_v["Estado"]=="Pagado")]["Total Cobrado ($)"].sum()
        transfer_total=df_v[(df_v["Método de Pago"]=="Transferencia")&(df_v["Estado"]=="Pagado")]["Total Cobrado ($)"].sum()
    else:
        cobrado_real=pendiente_cobro=ganancia_real=efectivo_total=transfer_total=0
    st.write("Estado de Caja General")
    c1,c2,c3=st.columns(3)
    c1.metric("Caja",f"${cobrado_real:,.0f}")
    c2.metric("Por Cobrar",f"${pendiente_cobro:,.0f}",delta_color="inverse")
    c3.metric("Ganancia Neta",f"${ganancia_real:,.0f}")
    st.divider()
    inv_total=sum(float(i.get('Costo_Compra',0)) for i in inventario)
    stock_actual_val=sum(float(i.get('Stock_Actual',0))*float(i.get('Costo_Unitario',0)) for i in inventario)
    costo_ventas=sum(float(v.get('Costo Producción ($)',0)) for v in ventas) if ventas else 0
    merma_teorica=inv_total-stock_actual_val-costo_ventas
    st.write("Análisis de Materia Prima y Pérdidas")
    cm1,cm2,cm3=st.columns(3)
    cm1.metric("Total Compras MP",f"${inv_total:,.0f}")
    cm2.metric("Stock Físico (Valor)",f"${stock_actual_val:,.0f}")
    cm3.metric("Merma Teórica",f"${merma_teorica:,.0f}")
    st.divider()
    col_graf,col_info=st.columns([2,1])
    with col_graf:
        st.write("Historial de Ventas")
        if ventas:
            df_g=pd.DataFrame(ventas)
            df_g["Total Cobrado ($)"]=pd.to_numeric(df_g["Total Cobrado ($)"],errors='coerce').fillna(0)
            st.line_chart(df_g.groupby("Fecha")[["Total Cobrado ($)"]].sum())
        else: st.info("No hay ventas.")
    with col_info:
        st.write("Pagos")
        st.write(f"Efectivo: ${efectivo_total:,.0f}")
        st.write(f"Transferencia: ${transfer_total:,.0f}")
elif menu=="Insumos":
    st.header("Ingreso de Materias Primas")
    foto_boleta=st.file_uploader("Sube boleta",type=["jpg","png","jpeg"])
    if foto_boleta:
        st.image(foto_boleta,width=250)
        if st.button("Leer Boleta"):
            try: api_key=st.secrets["GROQ_API_KEY"]
            except: api_key=None
            if api_key:
                with st.spinner("Analizando..."):
                    try:
                        img_b64=base64.b64encode(foto_boleta.getvalue()).decode('utf-8')
                        cliente=Groq(api_key=api_key)
                        prompt="""Eres un asistente experto en contabilidad de repostería en Chile. Lee esta boleta y extrae TODOS los productos legibles. Devuelve ÚNICAMENTE un arreglo JSON válido. Estructura: {"Nombre": "nombre genérico", "Marca": "marca", "Costo_Compra": numero_entero, "Cantidad_Compra": numero, "Unidad": "kg"}
                        REGLAS ESTRICTAS Y OBLIGATORIAS:
                        1. MONEDA CHILENA: Los puntos en los precios son separadores de miles. Devuelve SIEMPRE el "Costo_Compra" como número entero.
                        2. PESOS FALTANTES: Si un producto se usa por peso pero se cobra por unidades y NO DICE LOS GRAMOS, devuelve Cantidad original, Unidad: "unidades" y agrega " (FALTA PESO)" al Nombre.
                        3. UNIDADES permitidas: "gr", "kg", "ml", "L", "unidades", "paquete". Convierte lt->L, un->unidades, g->gr."""
                        respuesta=cliente.chat.completions.create(messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_b64}"}}]}],model="meta-llama/llama-4-scout-17b-16e-instruct",temperature=0)
                        res_txt = respuesta.choices[0].message.content
                        inicio = res_txt.find('[')
                        fin = res_txt.rfind(']')
                        if inicio != -1 and fin != -1: texto_json = res_txt[inicio:fin+1]
                        else: texto_json = res_txt.replace("```json","").replace("```","").strip()
                        datos_ia=json.loads(texto_json)
                        if isinstance(datos_ia,dict): datos_ia=[datos_ia]
                        for d in datos_ia: d["Unidad"]=normalizar_unidad(d.get("Unidad","unidades"))
                        st.session_state['lista_escaneada']=datos_ia
                        st.rerun()
                    except Exception as e: st.error(f"Error técnico en el escaneo: {e}")
    st.divider()
    if 'lista_escaneada' in st.session_state and st.session_state['lista_escaneada']:
        st.write("Revisión de Productos Detectados")
        items_con_problemas=[idx for idx,d in enumerate(st.session_state['lista_escaneada']) if "(FALTA PESO)" in d.get("Nombre","")]
        if items_con_problemas:
            st.error("La IA detectó productos que necesitan aclaración de peso.")
            for idx in items_con_problemas:
                item=st.session_state['lista_escaneada'][idx]
                with st.container(border=True):
                    st.warning(f"{item['Nombre']}")
                    st.write(f"Compraste {item['Cantidad_Compra']} unidades. ¿Cuánto pesa cada una?")
                    c1,c2,c3=st.columns([1,1,1])
                    peso_ind=c1.number_input("Peso unitario",min_value=0.1,value=250.0,key=f"peso_{idx}")
                    uni_ind=c2.selectbox("Medida",["gr","ml","kg","L"],key=f"uni_{idx}")
                    c3.write(""); c3.write("")
                    if c3.button("Corregir",key=f"btn_{idx}",use_container_width=True):
                        st.session_state['lista_escaneada'][idx]['Cantidad_Compra']=item['Cantidad_Compra']*peso_ind
                        st.session_state['lista_escaneada'][idx]['Unidad']=uni_ind
                        st.session_state['lista_escaneada'][idx]['Nombre']=item['Nombre'].replace(" (FALTA PESO)","").strip()
                        st.rerun()
            st.stop()
        df_escaneado=pd.DataFrame(st.session_state['lista_escaneada'])
        df_escaneado.insert(0,"Agregar",True)
        df_editado=st.data_editor(df_escaneado,hide_index=True,use_container_width=True,column_config={"Agregar":st.column_config.CheckboxColumn("¿Agregar?",default=True),"Costo_Compra":st.column_config.NumberColumn("Precio ($)",min_value=0,step=1),"Cantidad_Compra":st.column_config.NumberColumn("Cantidad",min_value=0.1),"Unidad":st.column_config.SelectboxColumn("Unidad",options=["gr","kg","ml","L","unidades","paquete"],required=True)})
        if st.button("Guardar Seleccionados"):
            items_a_guardar=df_editado[df_editado["Agregar"]==True]
            if not items_a_guardar.empty:
                nuevos_items=[]
                for _,fila in items_a_guardar.iterrows():
                    n_val=str(fila.get("Nombre","")).strip()
                    if not n_val or n_val.lower()=="nan": continue
                    m_val=str(fila.get("Marca","Genérico")).strip()
                    if m_val.lower()=="nan" or not m_val: m_val="Genérico"
                    c_val=float(fila.get("Costo_Compra",0))
                    can_val=float(fila.get("Cantidad_Compra",1.0))
                    u_val=normalizar_unidad(fila.get("Unidad","unidades"))
                    nuevos_items.append({"Nombre":n_val,"Marca":m_val,"Costo_Compra":c_val,"Cantidad_Compra":can_val,"Unidad":u_val,"Costo_Unitario":c_val/can_val if can_val>0 else c_val,"Stock_Actual":can_val,"Última_Compra":hoy})
                if nuevos_items:
                    actualizar_insumos_cloud(inventario+nuevos_items)
                    del st.session_state['lista_escaneada']
                    st.rerun()
        if st.button("Descartar todo"):
            del st.session_state['lista_escaneada']
            st.rerun()
    else:
        with st.form("form_insumos_manual",clear_on_submit=True):
            nombre=st.text_input("Nombre del Insumo")
            marca=st.text_input("Marca")
            costo=st.number_input("Precio ($)",min_value=0.0,format="%.0f")
            cantidad=st.number_input("Cantidad",min_value=0.1,value=1.0)
            unidad=st.selectbox("Unidad",["gr","kg","ml","L","unidades","paquete"],index=1)
            if st.form_submit_button("Guardar Manual") and nombre:
                actualizar_insumos_cloud(inventario+[{"Nombre":nombre,"Marca":marca.strip() or "Genérico","Costo_Compra":costo,"Cantidad_Compra":cantidad,"Unidad":normalizar_unidad(unidad),"Costo_Unitario":costo/cantidad,"Stock_Actual":cantidad,"Última_Compra":hoy}])
                st.rerun()
    st.divider()
    if inventario:
        st.dataframe(pd.DataFrame(inventario),hide_index=True)
        col_ed,col_el=st.columns(2)
        with col_ed:
            with st.expander("Editar"):
                s_ed=st.selectbox("Insumo a editar",[f"{x}: {i['Nombre']} ({i.get('Marca','Genérico')})" for x,i in enumerate(inventario)])
                idx_ed=int(s_ed.split(":")[0])
                it_ed=inventario[idx_ed]
                with st.form("f_ed_ins",clear_on_submit=True):
                    en=st.text_input("Nombre",value=it_ed['Nombre'])
                    em=st.text_input("Marca",value=it_ed.get('Marca','Genérico'))
                    ec=st.number_input("Precio ($)",min_value=0.0,value=float(it_ed.get('Costo_Compra',0)))
                    ecan=st.number_input("Cantidad",min_value=0.1,value=float(it_ed.get('Cantidad_Compra',1)))
                    ou=["gr","kg","ml","L","unidades","paquete"]
                    ua=it_ed.get('Unidad','unidades')
                    eu=st.selectbox("Unidad",ou,index=ou.index(ua) if ua in ou else 4)
                    est=st.number_input("Stock",min_value=0.0,value=float(it_ed.get('Stock_Actual',it_ed.get('Cantidad_Compra',1))))
                    if st.form_submit_button("Guardar"):
                        inventario[idx_ed].update({"Nombre":en,"Marca":em,"Costo_Compra":ec,"Cantidad_Compra":ecan,"Unidad":normalizar_unidad(eu),"Costo_Unitario":ec/ecan if ecan>0 else ec,"Stock_Actual":est})
                        actualizar_insumos_cloud(inventario)
                        st.rerun()
        with col_el:
            with st.expander("Eliminar"):
                b_sel=st.selectbox("Insumo a borrar",[f"{i['Nombre']} ({i.get('Marca','Genérico')})" for i in inventario])
                if st.button("Eliminar Definitivamente"):
                    actualizar_insumos_cloud([i for i in inventario if f"{i['Nombre']} ({i.get('Marca','Genérico')})"!=b_sel])
                    st.rerun()
elif menu=="Fichas Técnicas":
    st.header("Recetario")
    with st.form("f_nueva",clear_on_submit=True):
        n_r=st.text_input("Nombre Producto")
        c1,c2=st.columns(2)
        with c1: r_cant=st.number_input("Rendimiento",min_value=0.01,value=1.0)
        with c2: r_uni=st.selectbox("Unidad",["unidades","gr","kg","porciones"])
        cif=st.number_input("CIF ($)",min_value=0)
        if st.form_submit_button("Crear") and n_r:
            recetas[n_r]={'rendimiento_cantidad':r_cant,'rendimiento_unidad':r_uni,'cif':cif,'ingredientes':{}}
            actualizar_recetas_cloud(recetas)
            st.rerun()
    if recetas:
        st.divider()
        r_sel=st.selectbox("Editar",list(recetas.keys()))
        r_data=recetas[r_sel]
        with st.expander("Editar Generales"):
            with st.form("f_edit_base",clear_on_submit=True):
                n_nom=st.text_input("Nombre",value=r_sel)
                c1,c2=st.columns(2)
                with c1: n_cant=st.number_input("Rendimiento",min_value=0.01,value=float(r_data.get('rendimiento_cantidad',1.0)))
                with c2:
                    ou=["unidades","gr","kg","porciones"]
                    ua=r_data.get('rendimiento_unidad','porciones')
                    n_uni=st.selectbox("Unidad",ou,index=ou.index(ua) if ua in ou else 0)
                n_cif=st.number_input("CIF ($)",min_value=0,value=int(r_data['cif']))
                if st.form_submit_button("Guardar"):
                    if n_nom!=r_sel: recetas[n_nom]=recetas.pop(r_sel)
                    recetas[n_nom].update({'rendimiento_cantidad':n_cant,'rendimiento_unidad':n_uni,'cif':n_cif})
                    actualizar_recetas_cloud(recetas)
                    st.rerun()
        if r_data['ingredientes']: st.dataframe(pd.DataFrame([{'Insumo':k,'Cantidad':f"{v['cantidad']} {v['unidad']}"} for k,v in r_data['ingredientes'].items()]),hide_index=True)
        if inventario:
            with st.form("f_ing",clear_on_submit=True):
                i_s=st.selectbox("Ingrediente",[f"{i['Nombre']} ({i.get('Marca','Genérico')})" for i in inventario])
                cant=st.number_input("Cantidad",min_value=0.01)
                uni=st.selectbox("Unidad",["gr","kg","ml","L","unidades","paquete"])
                if st.form_submit_button("Añadir"):
                    recetas[r_sel]['ingredientes'][i_s]={'cantidad':cant,'unidad':uni}
                    actualizar_recetas_cloud(recetas)
                    st.rerun()
elif menu=="Rentabilidad":
    st.header("Análisis de Precios")
    if recetas:
        p_sel=st.selectbox("Producto",list(recetas.keys()))
        margen=st.slider("Margen (%)",10,80,40)/100
        t,p=obtener_costos_totales(p_sel)
        c1,c2,c3=st.columns(3)
        c1.metric("Costo Total",f"${t:,.0f}")
        c2.metric("Sugerido Completa",f"${t/(1-margen):,.0f}")
        c3.metric(f"Sugerido ({recetas[p_sel].get('rendimiento_unidad','unidad')})",f"${p/(1-margen):,.0f}")
elif menu=="Ventas y Caja":
    st.header("Registro de Ventas")
    if not recetas: st.info("Configura productos en Fichas Técnicas.")
    else:
        st.subheader("Asistente de Ventas")
        c_au,c_img=st.columns(2)
        with c_au: a_v=st.audio_input("Dictar Venta")
        with c_img: i_v=st.file_uploader("Pantallazo Chat",type=["jpg","png","jpeg"])
        if a_v or i_v:
            try: api_key=st.secrets["GROQ_API_KEY"]
            except: api_key=None
            if api_key:
                procesar = False
                if a_v and st.session_state.get('ult_au') != a_v.getvalue():
                    st.session_state['ult_au'] = a_v.getvalue()
                    procesar = True
                elif i_v and st.session_state.get('ult_im') != i_v.getvalue():
                    st.session_state['ult_im'] = i_v.getvalue()
                    procesar = True
                if procesar:
                    with st.spinner("Procesando..."):
                        try:
                            cliente=Groq(api_key=api_key)
                            txt_ex=""
                            if a_v and st.session_state.get('ult_au') == a_v.getvalue():
                                r_au=cliente.audio.transcriptions.create(file=("v.wav",a_v.getvalue()),model="whisper-large-v3")
                                txt_ex=r_au.text
                            elif i_v and st.session_state.get('ult_im') == i_v.getvalue():
                                b64=base64.b64encode(i_v.getvalue()).decode('utf-8')
                                r_img=cliente.chat.completions.create(messages=[{"role":"user","content":[{"type":"text","text":"Extrae todo el texto de esta imagen literalmente."},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],model="meta-llama/llama-4-scout-17b-16e-instruct",temperature=0)
                                txt_ex=r_img.choices[0].message.content
                            lista_prods=list(recetas.keys())
                            prompt=f"Analiza este texto: '{txt_ex}'. Devuelve SOLO un objeto JSON válido con esta estructura estricta: {{\"Producto\":\"nombre\",\"Formato\":\"Entero o Por porcion\",\"Cantidad\":numero,\"Cobrado\":numero,\"Pago\":\"Efectivo o Transferencia\"}}. El Producto DEBE ser el más similar a esta lista: {lista_prods}. Si el usuario no dice precio, pon 0."
                            res_json=cliente.chat.completions.create(messages=[{"role":"user","content":prompt}],model="llama-3.1-8b-instant",temperature=0,response_format={"type": "json_object"})
                            res_txt = res_json.choices[0].message.content
                            inicio = res_txt.find('{')
                            fin = res_txt.rfind('}')
                            if inicio != -1 and fin != -1: texto_json = res_txt[inicio:fin+1]
                            else: texto_json = res_txt.replace("```json","").replace("```","").strip()
                            dj=json.loads(texto_json)
                            st.session_state['v_prod']=dj.get("Producto",lista_prods[0])
                            st.session_state['v_form']="Entero" if "Entero" in str(dj.get("Formato","")) else "Por porcion"
                            st.session_state['v_cant']=int(dj.get("Cantidad",1))
                            st.session_state['v_cob']=int(dj.get("Cobrado",0))
                            st.session_state['v_pag']=dj.get("Pago","Efectivo")
                            st.success("¡Venta interpretada! Revisa el formulario abajo.")
                        except Exception as e: st.error(f"Error de IA: {e}")
        st.divider()
        s_id=len(ventas)
        with st.form("f_v",clear_on_submit=True):
            fecha=st.date_input("Fecha",date.today())
            d_p=st.session_state.get('v_prod',list(recetas.keys())[0])
            p_v=st.selectbox("Producto",list(recetas.keys()),index=list(recetas.keys()).index(d_p) if d_p in recetas else 0)
            u_txt=recetas[p_v].get('rendimiento_unidad','unidad')
            f_v=st.selectbox("Formato",["Entero",f"Por {u_txt}"],index=0 if st.session_state.get('v_form',"Entero")=="Entero" else 1)
            cant=st.number_input("Cantidad",min_value=1,value=st.session_state.get('v_cant',1))
            cobrado=st.number_input("Cobrado ($)",min_value=0,format="%d",value=st.session_state.get('v_cob',0))
            m_pago=st.selectbox("Pago",["Efectivo","Transferencia"],index=0 if st.session_state.get('v_pag',"Efectivo")=="Efectivo" else 1)
            status=st.selectbox("Estado",["Pagado","Pendiente"])
            obs=st.text_area("Observaciones")
            if st.form_submit_button("Registrar Venta"):
                t,p=obtener_costos_totales(p_v)
                c_asoc=(t if f_v=="Entero" else p)*cant
                f_rec=cant if f_v=="Entero" else cant/recetas[p_v].get('rendimiento_cantidad',1.0)
                for insumo_completo,datos_ing in recetas[p_v]['ingredientes'].items():
                    n_base=insumo_completo.split(" (")[0] if " (" in insumo_completo else insumo_completo
                    for i in reversed(range(len(inventario))):
                        if inventario[i]['Nombre']==n_base:
                            cu=datos_ing['cantidad']*f_rec
                            ur=datos_ing['unidad']
                            ui=inventario[i]['Unidad']
                            if ui=="kg" and ur=="gr": cu/=1000
                            elif ui=="gr" and ur=="kg": cu*=1000
                            elif ui=="L" and ur=="ml": cu/=1000
                            elif ui=="ml" and ur=="L": cu*=1000
                            inventario[i]['Stock_Actual']=max(0,float(inventario[i].get('Stock_Actual',0))-cu)
                            break
                actualizar_insumos_cloud(inventario)
                ventas.append({"ID Venta":s_id,"Fecha":str(fecha),"Producto":p_v,"Formato":f_v,"Cantidad":int(cant),"Total Cobrado ($)":float(cobrado),"Costo Producción ($)":round(c_asoc,0),"Ganancia Neta ($)":round(cobrado-c_asoc,0),"Método de Pago":m_pago,"Estado":status,"Observaciones":obs})
                actualizar_ventas_cloud(ventas)
                for k in ['v_prod','v_form','v_cant','v_cob','v_pag']: st.session_state.pop(k,None)
                st.rerun()
        if ventas:
            st.write("Historial")
            st.dataframe(pd.DataFrame(ventas),hide_index=True)
