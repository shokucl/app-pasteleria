# Bakery POS & Management System

[English Version](#english-version) | [Versión en Español](#spanish-version)

---

<a name="english-version"></a>
## Project Overview

**Language Context:** *The user interface, variables, and core logic are entirely in Spanish. This is due to its nature as a custom-built, functional application deployed for a local business.*

### System Description
A web application built with Python and Streamlit to centralize point-of-sale activities, dynamic recipe cost analysis, and smart inventory tracking for a bakery business.

### Origin & Zero-Cost Architecture
This software was developed to solve a real-world operational requirement while keeping infrastructure expenses at exactly zero. Alicia needed an efficient method to track expenses, calculate accurate production costs, and manage daily sales. As an entry point into software development and data management before transitioning to formal relational databases, the architecture creatively leverages free-tier services:
* **Headless Backend (No SQL required):** Google Sheets API serves as a lightweight, real-time synchronized database. The spreadsheet acts purely as an invisible backend; all operations and data management are handled exclusively through the dashboard interface, keeping the user entirely away from raw spreadsheets, while eliminating database hosting costs.
* **Free AI Integrations:** The Groq API provides high-speed, cost-free access to Llama-3 (for receipt reading via computer vision) and Whisper (for voice-to-text sales entry).
* **Zero-Install Cloud Deployment:** Hosted seamlessly on Streamlit Community Cloud. The system is accessed directly from a smartphone as a mobile web app via a live link (https://controlpasteleria.streamlit.app/), completely eliminating the need for local installations or server maintenance.

### Key Features
* **Computer Vision Inventory:** Extracts purchased items, quantities, and prices directly from receipt photos.
* **Smart Sales Input:** Logs transactions through voice memos or chat screenshot analysis.
* **Financial Engine:** Automatically calculates direct materials, labor rates (man-hours), overhead costs (CIF), and optimal retail prices.
* **Customer Management:** Tracks purchase history and key dates for client loyalty.

### Local Development Environment
While the application is hosted in the cloud, it can be run locally for testing and development purposes:

    git clone https://github.com/shokucl/app-pasteleria.git
    cd app-pasteleria
    pip install -r requirements.txt

Create environment variables in `.streamlit/secrets.toml`:

    url="YOUR_SPREADSHEET_URL"
    GROQ_API_KEY="YOUR_API_KEY"
    [usuarios]
    username="your_password"

Start the application:

    streamlit run appalc.py

### License
Copyright. All rights reserved. The use, modification, or commercial distribution of this source code is strictly prohibited.

---

<a name="spanish-version"></a>
## Resumen del Proyecto

### Descripción del Sistema
Una aplicación web desarrollada con Python y Streamlit para centralizar las operaciones de punto de venta, análisis dinámico de costos de recetas y seguimiento inteligente de inventario para un emprendimiento de repostería.

### Origen y Arquitectura de Costo Cero
Este software fue desarrollado para resolver un requerimiento operativo real manteniendo los gastos de infraestructura estrictamente en cero. Alicia necesitaba un método eficiente para llevar el control de los gastos, calcular con precisión los costos de producción y gestionar las ventas diarias. Como un proyecto de entrada al desarrollo de software y gestión de datos antes de dar el salto a bases de datos relacionales formales, la arquitectura aprovecha de forma creativa servicios gratuitos:
* **Backend Invisible (Sin SQL):** La API de Google Sheets funciona como una base de datos ligera y sincronizada. La hoja de cálculo actúa puramente como motor interno; todas las operaciones se realizan exclusivamente desde el panel visual, manteniendo al usuario final completamente alejado de planillas crudas, y eliminando por completo los gastos de hosting.
* **IA sin Costo:** La API de Groq proporciona acceso rápido y gratuito a Llama-3 (para leer boletas mediante visión computacional) y Whisper (para ingresar ventas por voz).
* **Despliegue en la Nube sin Instalación:** Alojado de forma nativa en Streamlit Community Cloud. El sistema se utiliza directamente desde el smartphone como una aplicación web móvil mediante un enlace directo (https://controlpasteleria.streamlit.app/), eliminando totalmente la necesidad de instalaciones locales.

### Funcionalidades Principales
* **Inventario por Visión Computacional:** Extrae artículos, cantidades y precios directamente desde fotografías de boletas.
* **Ingreso Inteligente de Ventas:** Registra transacciones mediante notas de voz o analizando capturas de pantalla de chats.
* **Motor Financiero:** Calcula materias primas, tarifas de mano de obra (H/H), costos indirectos de fabricación (CIF) y precios de venta óptimos.
* **Gestión de Clientes:** Mantiene el historial de compras y fechas clave de los clientes.

### Entorno de Desarrollo Local
Aunque el sistema opera en la nube, es posible ejecutarlo localmente para realizar pruebas o modificaciones:

    git clone https://github.com/shokucl/app-pasteleria.git
    cd app-pasteleria
    pip install -r requirements.txt

Crear variables de entorno en `.streamlit/secrets.toml`:

    url="URL_DE_TU_HOJA_DE_CALCULO"
    GROQ_API_KEY="TU_API_KEY"
    [usuarios]
    usuario="tu_contraseña"

Iniciar la aplicación:

    streamlit run appalc.py

### Licencia
Todos los derechos reservados. Queda estrictamente prohibido el uso, modificación o distribución comercial de este código fuente.
