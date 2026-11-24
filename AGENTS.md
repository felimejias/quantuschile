# 🚨 DIRECTIVA CRÍTICA DE COHERENCIA DE CÓDIGO Y CONTROL DE VERSIONES (QUANTUS CHILE SPA)

> [!IMPORTANT]
> **ARQUITECTURA DE TRES NIVELES (HA MULTI-CLOUD) Y MEMORIA COMPARTIDA**:
> 1. **MEMORIA MULTI-MODELO OBLIGATORIA (`LEDGER.md`)**: Toda IA (Antigravity, ChatGPT, Codex, OpenCode, Hermes) DEBE leer `LEDGER.md` antes de auditar, planificar o codificar. No duplicar tareas ya resueltas. Al finalizar, registrar la nueva fila inmutable.
> 2. **JERARQUÍA Y TOPOLOGÍA DE SERVIDORES (DESACOPLAMIENTO ESTRICTO)**:
>    - **Tier 1 (PRIMARIO WEB PÚBLICO Y EDGE API)**: **Oracle Cloud Santiago (`100.108.188.15` / `146.181.50.43`)**. Sede soberana de `quantuschile.cl`, portal web, landing pages, `/do`, `/licitaciones` y edge API. Opera 100% autónomo sin depender del servidor físico.
>    - **Tier 2 (HOT STANDBY CLOUD)**: **Microsoft Azure (`100.99.23.68` / `158.23.185.184`)**. Réplica en caliente y failover automático en el borde (Cloudflare Tunnel).
>    - **Tier 3 (CÓMPUTO ASÍNCRONO, BIG DATA Y ALMACÉN PESADO)**: **Servidor Físico Rancagua (`100.93.88.89` y LXC `100.117.44.3`)**. Confinado al 100% a tareas pesadas (Optuna, velas 15m, backtests, almacenamiento histórico ZFS y tareas en diferido). **ESTRICTAMENTE DESACOPLADO de la disponibilidad web pública**: si el servidor físico se apaga o pierde conectividad, el sitio web público jamás cae.
> 3. **REPOSITORIO CANÓNICO DE CÓDIGO WEB**:
>    - GitHub: `felimejias/quantuschile` (rama `main`).
>    - Directorio de producción en servidores: `/opt/quantus/portal/`.
> 4. **ORDEN DE DESPLIEGUE WEB OBLIGATORIO**:
>    - Todo cambio a frontend, plantillas (`templates/`), estáticos (`static/`) o rutas web debe desplegarse **PRIMERO en Oracle Cloud (Tier 1)**, **SEGUNDO en Azure (Tier 2)** y registrarse en el repositorio GitHub `felimejias/quantuschile`.
> 5. Jamás debes sobrescribir o subir archivos locales a los servidores sin haber verificado primero la versión remota activa usando comandos SSH y comparado las diferencias.
> 
> 6. **PROTOCOLO OBLIGATORIO DE CONSULTA DE LICITACIONES**:
>    Ante cualquier solicitud del operador sobre "licitaciones", "vencimientos", "próximas a cerrar" o "postulaciones", el agente **TIENE ESTRICTAMENTE PROHIBIDO** consultar APIs externas (Mercado Público) o hacer búsquedas en frío sin orden expresa.
>    * **Paso 1 Obligatorio**: Leer físicamente el archivo `quantus/licitaciones/INDICE_EXPEDIENTES_LOCALES.md` y revisar las carpetas locales en `quantus/licitaciones/01_LISTAS_PARA_REVISION/`.
>    * Solo si el operador ordena expresamente *"escanear el mercado"*, *"buscar nuevas licitaciones"* o *"correr el radar"*, se ejecutará la prospección externa.
> 
> 7. **DIRECTIVA SUPREMA DE SEPARACIÓN DE AUDITORÍA MULTI-MODELO (ANTIGRAVITY NUNCA SE AUTO-AUDITA)**:
>    Antigravity opera como constructor, redactor técnico y compilador determinista de expedientes y código. **Antigravity TIENE ESTRICTAMENTE PROHIBIDO actuar como auditor o juez de sus propios artefactos**. La auditoría adversarial vinculante, el contraste riguroso contra bases/foro y el dictamen de admisibilidad DEBEN ser ejecutados exclusivamente por **OpenCode** o **Hermes en el servidor** con sus modelos más completos.
> 
> **MATRIZ DE CONEXIÓN SSH DIRECTA A NODOS**:
> *   **Tier 1 (Oracle Cloud)**: `ssh -i ~/.ssh/quantus_oracle_standby_ed25519 ubuntu@100.108.188.15` (sudo sin password)
> *   **Tier 2 (Azure Hot Standby)**: `ssh -i ~/.ssh/quantus_ops_20261025 root@100.99.23.68`
> *   **Tier 3 (Servidor Físico)**: Gateway `ssh root@100.93.88.89` / LXC `ssh root@100.117.44.3`

---

# 🛡️ MARCO DE INTEGRIDAD DE DATOS, NORMAS ISO Y MEMORIA OPERATIVA (QUANTUS CHILE SPA)

Este compendio fija la arquitectura técnica, las políticas de seguridad de la información (ISO/IEC 27001 / 27701), gestión de calidad (ISO 9001) y la protección de datos personales (Ley N° 21.719 de Chile) que **Antigravity y todos los agentes corporativos deben obedecer estrictamente sin excepción**.

---

## 🏛️ SECCIÓN 1 — Principio Rector y Arquitectura de Datos Maestra (Esquema Canónico v4)

**Existe una sola fuente de verdad para la identidad de personas y empresas: la tabla `CLIENTES`.**
Todos los módulos de negocio (Diario Oficial, Remates Judiciales, Mercado Público / Licitaciones, Marcas INAPI, Empleos Públicos, ERP Proveedores, Facturación y Ley 21.719) son **tablas satélite que referencian a `CLIENTES` por `id_cliente` (FK)**. Ningún módulo tiene autoridad para duplicar, alterar, reinventar o borrar el nombre, correo o celular de una persona.

### Esquema Canónico Relacional PostgreSQL 14+ / SQLite WAL:
1. **Tabla Maestra `CLIENTES` (Identidad Central)**:
   - `id_cliente SERIAL PRIMARY KEY`
   - `rut VARCHAR(14) NOT NULL UNIQUE` (Validación Módulo 11 + Formato: `14.011.762-5` o `76.123.456-7`)
   - `tipo_persona VARCHAR(10) NOT NULL CHECK (tipo_persona IN ('natural','juridica'))`
   - `nombre_razon_social TEXT NOT NULL`
   - `correo_principal TEXT NOT NULL` (Correo oficial o DTE, índice `LOWER`)
   - `celular_principal TEXT`, `direccion TEXT`, `comuna TEXT`
   - `estado VARCHAR(15) NOT NULL DEFAULT 'lead' CHECK (estado IN ('lead','activo','suspendido','cancelado'))`
   - `fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now()`
   - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` (Trigger `set_updated_at()`)

2. **Evidencia Documental (`uploaded_documents` — Fuente Única de Archivos/Hashes)**:
   - `id_documento SERIAL PRIMARY KEY`, `id_cliente INTEGER REFERENCES clientes(id_cliente) ON DELETE SET NULL`
   - `modulo VARCHAR(30) NOT NULL CHECK (modulo IN ('diario_oficial','remates','licitaciones','marcas_inapi','empleos_publicos','erp','asesoria_ley21719','arcop'))`
   - `tipo_documento VARCHAR(40) NOT NULL` (`'logo'`, `'poder_simple'`, `'cv'`, `'ci_anverso'`)
   - `file_name TEXT`, `file_path TEXT`, `file_sha256 CHAR(64) NOT NULL` (Indexado), `mime_type TEXT`, `size_bytes BIGINT`
   - `scan_status VARCHAR(15) NOT NULL DEFAULT 'pendiente' CHECK (scan_status IN ('pendiente','limpio','infectado','error'))`
   - `created_at TIMESTAMPTZ DEFAULT now()`

3. **Auditoría Polimórfica (`audit_events` — Trazabilidad Inmutable ISO 27001)**:
   - `id_evento BIGSERIAL PRIMARY KEY`, `id_cliente INTEGER REFERENCES clientes(id_cliente) ON DELETE SET NULL`
   - `actor TEXT NOT NULL`, `action TEXT NOT NULL`, `object_type TEXT NOT NULL`, `object_id TEXT`, `payload_json JSONB`, `ip_address INET`
   - `"timestamp" TIMESTAMPTZ NOT NULL DEFAULT now()` (Indexado DESC)

4. **Portal ARCOP (`arcop_solicitudes` — Ley N° 21.719)**:
   - `id_solicitud SERIAL PRIMARY KEY`, `folio VARCHAR(40) NOT NULL UNIQUE` (Folio Criptográfico)
   - `id_cliente INTEGER REFERENCES clientes(id_cliente) ON DELETE SET NULL`, `id_doc_identidad INTEGER REFERENCES uploaded_documents(id_documento) ON DELETE SET NULL`
   - `tipo_derecho VARCHAR(20) NOT NULL CHECK (tipo_derecho IN ('acceso','rectificacion','supresion','oposicion','portabilidad','bloqueo'))`
   - `canal_ingreso VARCHAR(20) DEFAULT 'portal'`, `fecha_ingreso TIMESTAMPTZ DEFAULT now()`
   - `plazo_limite TIMESTAMPTZ NOT NULL` (30 días corridos Art. 11 / 2 días hábiles bloqueo Art. 8° ter)
   - `prorroga_aplicada BOOLEAN DEFAULT false`, `fecha_respuesta TIMESTAMPTZ`
   - `estado VARCHAR(25) DEFAULT 'en_proceso' CHECK (estado IN ('en_proceso','resuelto_favorable','resuelto_desfavorable','vencido'))`
   - `respuesta_texto TEXT`, `created_at TIMESTAMPTZ DEFAULT now()`

5. **Suscripciones y Billing Centralizado (`suscripciones`)**:
   - `id_suscripcion SERIAL PRIMARY KEY`, `id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT`
   - `modulo VARCHAR(30) NOT NULL CHECK (modulo IN ('diario_oficial','remates','licitaciones','marcas_inapi','empleos_publicos','erp','asesoria_ley21719'))`
   - `plan VARCHAR(30) NOT NULL`, `precio_clp INTEGER NOT NULL`
   - `payment_mode VARCHAR(20) DEFAULT 'mensual' CHECK (payment_mode IN ('mensual','anual','unico'))`
   - `fecha_inicio DATE NOT NULL`, `fecha_renovacion DATE`
   - `estado VARCHAR(15) DEFAULT 'activa' CHECK (estado IN ('activa','pausada','cancelada','vencida'))`
   - `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at TIMESTAMPTZ DEFAULT now()`

6. **Tablas Satélite de Configuración (Solo Parámetros de Servicio vinculados por `id_suscripcion` ON DELETE CASCADE)**:
   - `diario_oficial_config`: `id_config` (PK), `id_suscripcion` (FK UNIQUE), `rut_titular`.
   - `diario_oficial_watch_targets`: `id_target` (PK), `id_config` (FK), `rut_objetivo`, `palabra_clave` (Indexado B-Tree LOWER + GIN Trigram `pg_trgm`).
   - `remates_config`: `id_config` (PK), `id_suscripcion` (FK UNIQUE), `region_interes`, `tipo_bien` (`inmueble`|`vehiculo`|`otro`), `monto_postura_minima`.
   - `licitaciones_config`: `id_config` (PK), `id_suscripcion` (FK UNIQUE), `rut_empresa`, `rubro`, `region_cobertura`, `monto_minimo`.
   - `marcas_inapi_config`: `id_config` (PK), `id_suscripcion` (FK UNIQUE), `marca_monitoreada`, `tipo_marca`, `clase_niza` (CHECK 1-45), `direccion_titular`, `comuna_titular`, `id_doc_logo` (FK), `id_doc_poder_simple` (FK), `id_doc_inicio_actividades` (FK).
   - `empleos_publicos_config`: `id_config` (PK), `id_suscripcion` (FK UNIQUE), `id_doc_cv` (FK), `cargo_buscado`, `titulos`, `region_residencia`, `renta_minima`, `match_status`.

7. **ERP y Facturación (Aislamiento Multi-Tenant Estricto)**:
   - `erp_proveedores`: `id_proveedor` (PK), `id_cliente` (FK ON DELETE RESTRICT), `rut_proveedor`, `razon_social`, `categoria_insumo`, `banco`, `cuenta_transferencia`, `plazo_pago_dias`, `UNIQUE(id_cliente, rut_proveedor)`, `UNIQUE(id_proveedor, id_cliente)`.
   - `erp_clientes_comerciales`: `id_cliente_comercial` (PK), `id_cliente` (FK ON DELETE RESTRICT - Dueño de la cuenta), `rut_cliente_final`, `razon_social`, `correo`, `plazo_pago_dias`.
   - `erp_facturas_compras`: `id_factura` (PK), `id_cliente` (FK ON DELETE RESTRICT), `id_proveedor` (FK ON DELETE RESTRICT), `folio_dte`, `tipo_documento` (33/34/61), `monto_neto`, `monto_iva` (DEFAULT 0), `monto_total`, `fecha_emision`, `fecha_pago`, `estado`, `CHECK (monto_total = monto_neto + monto_iva)`, `CONSTRAINT fk_factura_proveedor_mismo_cliente FOREIGN KEY (id_proveedor, id_cliente) REFERENCES erp_proveedores(id_proveedor, id_cliente) ON DELETE RESTRICT`, `CONSTRAINT uq_proveedor_dte UNIQUE (id_proveedor, folio_dte, tipo_documento)`.

---

## 🔒 SECCIÓN 2 — Matriz de Control, Evidencia y Normas ISO

### Matriz de Cumplimiento Técnico y Operativo:

| Norma / Cláusula | Control Exigido | Evidencia en Runtime | Responsable | Frecuencia | Prueba de Validación |
|---|---|---|---|---|---|
| **ISO 27001 A.5.15** | Control de Acceso e Identificación Única | Clave única normalizada `RUT` con validación Módulo 11 en tabla `CLIENTES`. Sin sesión anónima en PII. | Backend / Auth Module | En cada transacción | Query SQL `SELECT rut, count(*) GROUP BY rut HAVING count(*)>1` = 0. |
| **ISO 27001 A.8.10** | Eliminación Segura vs. Retención Legal | Daemon `purge_cancelled_accounts_30d.py` ejecutando purga de leads huérfanos tras 30d y anonimización de clientes con DTE. | Cron Job / Python Daemon | Diario a las 04:00 AM | Ejecución con `--dry-run` comprobando separación leads vs. clientes con DTE/suscripciones. |
| **ISO 27001 A.8.11** | Cifrado y Protección Criptográfica | TLS 1.3 / HSTS Cloudflare en tránsito + hashes SHA-256 en archivos `uploaded_documents`. | Gateway / Nginx / Flask | Continuo 24/7 | `curl -I https://www.quantuschile.cl` reportando HSTS estricto. |
| **ISO 27001 A.8.12** | Prevención de Fugas y Aislamiento Multi-Tenant | Módulos satélites aislados; FK compuesta `(id_proveedor, id_cliente)` en ERP para evitar contaminación cruzada. | Arquitectura BD | En cada query | Verificación de esquemas satélites sin duplicación de emails ni cruce de proveedores. |
| **ISO 27701 (PII)** | Principio de Minimización y Trazabilidad | Consentimientos registrados con IP, timestamp ISO y versión de política en `audit_events`. | Form Handlers / DB | En cada alta | Consulta a `audit_events` verificando registros de consentimiento. |
| **Ley N° 21.719 (ARCOP)**| Gestión de Derechos ARCOP (Arts. 11 y 8° ter) | Endpoint `/api/arcop/solicitud` con cómputo estricto de 30 días corridos (general) / 2 días hábiles (bloqueo) y folio SHA-256. | Portal ARCOP / Legal | Continuo | Emisión de solicitud generando folio criptográfico y fecha límite conforme a Ley 21.719. |
| **ISO 9001 Cl. 8.5** | Trazabilidad y Cero Datos Fabricados | Prohibición absoluta de inferir o autocompletar. Si no está, es `DATO NO ENCONTRADO`. | Agentes IA / Antigravity | Permanente | Auditoría de respuestas sin campos asumidos ni proxies. |
| **ISO 22301 / ISO 27001 A.5.24-A.5.28** | Gestión de Incidentes, Control de Fallos y DR | Procedimiento maestro SOP_CONTROL_FALLOS_ISO.md obligatorio para IA y operadores humanos. RTO < 15m en SEV-1. | Antigravity / DevOps / Sysadmin | En cada falla o alarma | Ejecución de ciclo 6 fases con registro inmutable en post-mortem y audit_events. |
| **ISO 9001 Cl. 7.1.5** | Respaldos Inmutables de Base de Datos | `quantus-backup.timer` a las 03:15 AM + `daily_backup_quantus.sh` a las 03:00 AM con rotación 30d. | Systemd Timer / Bash | Diario | Verificación de snapshot `.sql.gz` y `.db` en `/opt/quantus/backups/`. |

---

## 🚨 SECCIÓN 3 — Reglas Duras de Identidad y Memoria (Inviolables)

### REGLA 0 — Nunca inventar, nunca autocompletar
Si un dato (RUT, nombre, correo, celular, empresa) no está literalmente en el registro que estás leyendo, **no existe** para ti. No lo completes por patrón, por parecido, ni por lo que "normalmente correspondería". Si falta, el resultado es: `DATO NO ENCONTRADO`, nunca un valor inventado.

### REGLA 1 — La identidad se resuelve por clave única, nunca por nombre o apellido
El **RUT** (o el **correo exacto registrado** en el módulo correspondiente) es la única clave válida para identificar a una persona o empresa. Dos personas con los mismos apellidos y distinto nombre son **dos registros completamente distintos y no relacionados**.

### REGLA 2 — Cada módulo es una fuente de datos aislada
No mezcles campos ni infieras datos de un módulo usando información de otro, salvo que el usuario esté vinculado explícitamente por el mismo RUT en `CLIENTES`.

### REGLA 3 — CVs y documentos: almacenamiento físico y extracción exacta
Los currículums deben residir físicamente en `/mnt/proyectos/felipe/quantus_empleos_publicos/storage_cvs/` y `storage_cvs/` con nombre único `{rut}_{timestamp}_{sha256[:8]}_{filename}`. Toda extracción de competencias, títulos, teléfonos y RUTs debe realizarse directamente desde los archivos PDF/DOCX originales mediante parsers validados (`pypdf`, `python-docx`).

### REGLA 4 — Reglas de Lectura y Escritura
* **Al guardar**: Normalizar y validar RUT (`14.011.762-5`), buscar en `CLIENTES` (crear si no existe), y guardar en la tabla satélite con `id_cliente` o `id_suscripcion`.
* **Al leer**: Buscar por RUT exacto. Traer datos de contacto **solo desde `CLIENTES`**. Traer parámetros de servicio de su tabla satélite.

### REGLA 5 — Prioridad Absoluta de Evidencia Visual e Imágenes
Si el usuario envía una imagen o captura de pantalla, **ES LO PRIMERO Y OBLIGATORIO QUE DEBES MIRAR, ANALIZAR Y CONTRASTAR** antes de ejecutar scripts o sacar conclusiones ciegas. Queda terminantemente prohibido ignorar los datos visibles en la imagen para confiar en cálculos aislados o intuición del modelo. La evidencia visual entregada por el usuario manda sobre cualquier simulación ciega.

### REGLA 6 — Prohibición de Promesas de WhatsApp Automático
Queda estrictamente prohibido prometer alertas automáticas de WhatsApp en correos, plantillas o formularios mientras la API Meta Cloud esté en verificación comercial. El canal oficial de entrega y alertas 24/7 es **Correo Electrónico Oficial**.


### REGLA 7 — Puerta Única de Acceso POS/ERP y Prohibición Absoluta de Login Interno en /app
* **Puerta de Entrada Exclusiva**: La única página autorizada para ingresar credenciales al Punto de Venta / ERP es `https://www.quantuschile.cl/punto-de-venta/acceso`. Ningún usuario ni operador ingresa por otra vía.
* **Prohibición de Formulario de Login en `/app`**: Queda terminantemente prohibido renderizar cualquier formulario o pantalla de login interna dentro de `/app` (pantalla oscura con "Quantus App - Centro de Mando Inteligente"). Esa pantalla no debe existir bajo ningún concepto.
* **Redirección de Acceso No Autenticado**: Si un usuario entra a `/app` sin sesión activa, o con ticket SSO inválido/expirado, el frontend debe expulsar y redirigir inmediatamente a `/punto-de-venta/acceso`.
* **Cierre Automático por Inactividad (Tiempo de No Uso)**: Si la aplicación permanece 15 minutos sin interacción del usuario (sin movimiento de mouse, teclas, touch, clics ni scroll), la sesión se elimina localmente y se redirige automáticamente al usuario a `https://www.quantuschile.cl/punto-de-venta/acceso?timeout=1`, mostrando la alerta correspondiente.
* **Cierre de Sesión (Salir)**: La opción "Salir" en el menú lateral o botón de logout siempre destruye la sesión y redirige inmediatamente a `https://www.quantuschile.cl/punto-de-venta/acceso?logout=1`.



### REGLA 8 — Liberación Universal y Acceso Gratuito a Empleos Públicos
* **Búsqueda y Convocatorias Libres**: El portal de convocatorias laborales (`/empleos-publicos/`) opera bajo modalidad abierta y 100% gratuita para la ciudadanía. Queda prohibido bloquear búsquedas por cuota de IP o censurar URLs oficiales y bases de concurso.
* **Analista de Inteligencia Artificial Libre**: El motor de calce curricular asistido por IA (`quantus_ai.py` con Nemotron 120B/550B) está liberado para todos los postulantes, requiriendo únicamente el consentimiento explícito Ley N° 21.719 al cargar el CV.

### REGLA 9 — Prohibición Absoluta de Venta de Humo y Mocks de Hardware Inexistente (Carta Magna P0)
* **Cero Fabricación Ficticia de Hardware**: Quantus Chile SpA es una compañía de SOFTWARE en la nube y servicios de inteligencia de datos. **NO fabrica, NO importa y NO vende hardware físico, terminales POS ni impresoras térmicas**.
* **Prohibición de Generación Audiovisual Ficticia**: Queda estrictamente prohibido a cualquier agente (Antigravity, Hermes, OpenCode, Codex) generar o aprobar videos, reels o imágenes publicitarias que simulen máquinas POS físicas o impresoras con la marca Quantus.
* **Naturaleza Real de Quantus POS**: Es una plataforma web/app accesible desde tablet, smartphone o PC (`https://www.quantuschile.cl/punto-de-venta`). Se integra con las máquinas de cobro que el cliente ya tiene (Mercado Pago Point, Transbank o SumUp). Tampoco emite boletas ni facturación electrónica DTE.
* **Contenido Audiovisual Autorizado**: Todo video o material gráfico debe mostrar exclusivamente la **interfaz real del software Quantus** (pantalla táctil del navegador) o el dolor operativo real de la pyme (desorden en inventario, cuadratura de caja). Cero venta de humo.

---



## 💾 SECCIÓN 4 — Memoria Operativa y Padrón de Titulares Verificados

### 1. Titulares Oficiales Registrados en `CLIENTES`:
* **Felipe Esteban Mejías González**
  * **RUT Real**: `14.011.762-5`
  * **Correo Principal**: `felipe.mejias.g@gmail.com`
  * **Teléfono**: `+56 9 7548 0746`
  * **Ubicación**: Rancagua (Región del Libertador Bernardo O'Higgins / Codelco El Teniente)
  * **Especialidades**: Técnico en Minas / Control de Flota & Especialista en Automatización, IA y Control de Gestión.
* **Lorena Andrea Cifuentes Matus de la Parra**
  * **RUT**: `16.541.239-4`
  * **Correo Principal**: `lcifuentesm@hotmail.com` (Secundario: `lorenacifuentesm@gmail.com`)
  * **Teléfono**: `+56 9 3239 7971`
  * **Ubicación**: Curicó (Región del Maule)
  * **Especialidades**: Ingeniera en Prevención de Riesgos (U. Aconcagua) | Contador General (CFT San Agustín).
* **Raúl Antonio Alfaro Mancilla**
  * **RUT**: `14.152.720-7`
  * **Correo Principal**: `raul.alfaro198100@gmail.com` (Secundario: `raul.alfaro@hotmail.com`)
  * **Teléfonos**: `+56 9 7989 5677` / `+56 9 9470 7028`
  * **Ubicación**: Rancagua / Machalí
  * **Especialidades**: Ingeniero en Mina (IPG) | Técnico Nivel Superior en Mina.

### 2. Servicios de Fondo y Automatizaciones Activas en Servidor:
* **03:15 AM**: `quantus-backup.timer` (Respaldo inmutable + SHA-256 + 30d rotación).
* **04:00 AM**: `purge_cancelled_accounts_30d.py` (Purga 30 días Ley 21.719 para leads / Anonimización para clientes con DTE).
* **07:00 AM**: `quantus-licitaciones-worker.timer` (Ingesta diaria API ChileCompra + Matching 2 Etapas Licitaciones).
* **09:30 AM & 14:30 PM**: `quantus-do-downloader.timer` (Descarga automática y continua de la edición diaria del Diario Oficial + Ingesta en do_historico.db).
* **08:30 AM**: `worker_daemon.py --digest` (Resumen matutino diario con Top 10 convocatorias vigentes).
* **Cada 2 Horas**: `quantus-empleos-worker.timer` (Sincronización multi-entidad y alerta en caliente ante nuevas vacantes).
* **Cada Hora (:55)**: `quantus-empleos-ai.timer` (Analista IA de Empleos Públicos · Calce curricular y evaluación automática de vacantes vigentes).
* **Sábados 15:30 PM (1h post edición Diario Oficial)**: quantus-do-weekly-clear.timer (Reporte Semanal "Sin Incidencias" a suscriptores activos Diario Oficial).

---

## 📬 SECCIÓN 5 — Protocolo Canónico de Correos de Bienvenida (Los 2 Formatos Oficiales)

> [!IMPORTANT]
> **REGLA SUPREMA DE COMUNICACIONES DE BIENVENIDA**:
> Queda terminantemente prohibido inventar textos inline o improvisar correos de bienvenida. Toda activación de Diario Oficial debe utilizar obligatoriamente la plantilla canónica `communications/templates/diario_oficial_email_activacion.html` bajo la lógica estricta de **2 Formatos**:

### 1. Estructura Común Obligatoria (Ambos Formatos):
1. **Header Institucional**: `QUANTUS CHILE` | `Radar Diario Oficial 24/7 · Membresía Activa` | Badge verde `ACTIVO`.
2. **Tabla de Parámetros Activos**: Plan contratado, RUT monitoreado, Vigencia, Correo oficial y Estado `ACTIVO`.
3. **Bloque: ¿Cómo y cuándo recibirás nuestras notificaciones?**:
   * 🎁 **Beneficio de Bienvenida (Auditoría Retroactiva 9 Días o Ampliada por Convenio Jurídico)**: Todo nuevo suscriptor cuenta con una revisión de cortesía de los 9 días anteriores a su fecha de registro en las ediciones del Diario Oficial (plazo procesal legal oportuno de 3 a 5 días hábiles para ejercer defensa) para certificar que ingresa con balance limpio o alertarle de cualquier publicación reciente. Si el suscriptor ingresa un **Código de Convenio Jurídico** (tabla `convenios_juridicos`), la ventana de auditoría se amplía automáticamente a **30 o 60 días corridos** en cortesía con el estudio jurídico aliado.
   * 🚨 **Alerta Inmediata**: Aviso al instante ante cualquier publicación detectada con extracto y PDF adjunto.
   * 📭 **Bandeja Limpia**: Cero spam o correos diarios vacíos si no hay publicaciones.
   * 🛡️ **Reporte Semanal**: Reporte los fines de semana (*"Sin Incidencias"*) acreditando la continuidad del rastreo.
4. **Ecosistema y Soluciones Estratégicas**:
   * 💻 **1. Quantus POS & Agentes IA**: Integración directa con máquinas de cobro presencial (Mercado Pago, Transbank, SumUp) —*aclarando que NO emitimos boletas ni facturación electrónica DTE*— y Agentes IA para control predictivo de stock y quiebres.
   * ⚖️ **2. Asesoría Especializada en Ley N° 21.719 (Protección de Datos)**: Asesoría integral + Enlace directo al [Checklist Interactivo](https://www.quantuschile.cl/checklist-cumplimiento-ley-proteccion-datos-chile).
   * 🏛️ **3. Radar Mercado Público**: Alertas de licitaciones y compras ágiles.
   * 🛡️ **4. Custodia de Marca INAPI**: Vigilancia y defensa de marcas comerciales.
   * 🔨 **5. Radar Remates Judiciales**: Oportunidades de inmuebles y vehículos bajo tasación.
5. **Pie de Firma Institucional**: Quantus Chile SpA · RUT `78.478.612-9` · Rancagua · Soporte: `contacto@quantuschile.cl` · Privacidad (ARCO): `privacidad@quantuschile.cl`.

### 2. Diferenciación Estricta de los 2 Formatos:

* 🟡 **FORMATO 1 — Con Observación de Identidad (`nombre_incompleto = True`)**:
  * **Condición**: Para personas naturales que no completen sus 2 nombres y 2 apellidos (`len(tokens) < 4`, es decir 1, 2 o 3 tokens, ej. solo *"Samuel"*, *"Sergio Burgos"* o *"Claudio Vasquez Faundez"* donde falta el segundo nombre o segundo apellido).
  * **Contenido Adicional**: Inserta el recuadro ámbar de advertencia:
    > *🔍 Validación de Identidad: ¿Tienes un segundo nombre? En tu registro figura un nombre parcial. Si tu nombre legal es ese, no requieres hacer nada. Si tienes un segundo nombre en tu cédula, respóndenos indicándolo. ¿Por qué? La IA de Quantus cruza datos por RUT y por Nombre. Dado que el Diario Oficial a veces presenta erratas en los números de RUT, tener tu nombre legal completo exacto evita confusiones con homónimos y garantiza recibir exclusivamente las publicaciones pertinentes.*

* 🟢 **FORMATO 2 — Todo Correcto (`nombre_incompleto = False`)**:
  * **Condición**: El usuario registró sus nombres y dos apellidos completos (ej. *"Samuel Armando Pizarro Fernández"*).
  * **Contenido**: El bloque de observación de homonimia se omite por completo y el correo sale 100% limpio y directo con la confirmación de membresía y el ecosistema.

---



### 3. Arquitectura Canónica de Envío de Correos (Cloudflare Email Routing + Relay SMTP Personal):
> [!IMPORTANT]
> **REGLA SUPREMA DE INFRAESTRUCTURA DE CORREO ELECTRÓNICO (CERO GOOGLE WORKSPACE)**:
> 1. **Google Workspace ($$ pagado) está CANCELADO permanentemente**. La cuenta `contacto@quantuschile.cl` NO es una cuenta de Google Workspace activa y está terminantemente prohibido intentar autenticarse en SMTP con `contacto@quantuschile.cl` directamente en `smtp.gmail.com` (arrojará bloqueo 534 WebLoginRequired).
> 2. **Recepción Inbound (Cloudflare Email Routing)**: Cloudflare enruta automáticamente todas las casillas del dominio (`contacto@quantuschile.cl`, `privacidad@quantuschile.cl`, `fmejias@`, etc., y Catch-all) directamente hacia la bandeja de Gmail personal `felipe.mejias.g@gmail.com` ($0 USD).
> 3. **Envío Outbound (Relay SMTP Autorizado)**:
>    * El backend (`mailer.py`) autentica contra `smtp.gmail.com:587` usando la cuenta autorizada `GMAIL_AUTH_USER=felipe.mejias.g@gmail.com` y su Contraseña de Aplicación `GMAIL_APP_PASSWORD="[SECRETO EXTERNO: leer entorno protegido]"`.
>    * Las cabeceras `From:` y `Reply-To:` se configuran siempre con la identidad corporativa oficial: `Quantus Chile <contacto@quantuschile.cl>`.
>    * Los clientes visualizan el correo como proveniente de `contacto@quantuschile.cl` y al responder, el correo ingresa por Cloudflare Email Routing directo a la bandeja personal sin exponerla.
> 4. **Reporte Semanal de Tranquilidad ("Sin Incidencias")**:
>    * Se despacha automáticamente cada **Sábado a las 15:30 CLT** (1 hora después de la última edición del Diario Oficial procesada a las 14:30) vía `quantus-do-weekly-clear.timer` y `scripts/run_weekly_clear_report.py`.
>    * Emite el reporte preventivo a todos los clientes activos que no hayan registrado alertas legales durante la semana, confirmando que el rastreo 24/7 sigue activo con el badge verde `SIN INCIDENCIAS`.

---

## 💾 SECCIÓN 5 — Política de Almacenamiento y Cómputo Asimétrico (On-Premise vs. Cloud)

### 1. Principio de Carga y Cómputo Asimétrico:
* **Servidor Físico On-Premise (100.117.44.3 - Big Data, Cómputo Pesado & Cold Storage)**:
  - Concentra el 100% de las cargas de almacenamiento pesado y crecimiento continuo:
    1. Respaldos históricos inmutables (.sql.gz, snapshots de BD con rotación 30d).
    2. Big Data cuantitativo: Millones de velas de 15m, series de tiempo históricas, datasets de Optuna.
    3. Almacenamiento físico de documentos pesados: PDFs, contratos, CVs de clientes (storage_cvs/).
    4. Bitácoras y logs consolidados de auditoría.
    5. Destino de descarga automática de la nube en: `/opt/quantus/backups/cloud_offload/`.
  - **Ejecutor Exclusivo de Cómputo Pesado e Inteligencia**:
    - **100% de las Pruebas de Estrés (Stress Testing)**: Carga masiva de base de datos, pruebas de concurrencia extrema, benchmarks de I/O.
    - **100% de los Backtests Cuantitativos**: StratOS 32, Gaussian Bot V13, Flash Scalp Pro (estudios de 1.000.000 trials Optuna TPE, simulaciones Monte Carlo de 250 corridas sobre universo 772 pares Bitget 15m).
    - **Entrenamiento y Re-optimización de Modelos**: GPU/CPU multihilo local sin restricción.
* **Nodos Cloud (Oracle 146.181.50.43 y Azure 158.23.185.184 - Lean Edge Execution)**:
  - Mantienen una huella de disco y memoria mínima y quirúrgica (< 15-25% disco, < 50% RAM):
    1. Código ejecutable esencial: Nginx, Quantus ERP V1, portales web (quantuschile.cl, biobelle.cl), APIs y scrapers livianos.
    2. Tablas maestras activas para continuidad operativa 24/7 (CLIENTES y parámetros satélites vigentes).
    3. Prohibido retener respaldos históricos o acumular logs locales pesados en la nube.
  - **PROHIBICIÓN ESTRICTA DE BACKTESTS Y STRESS TESTING EN CLOUD**:
    - Queda terminantemente prohibido ejecutar backtests, optimizaciones de hiperparámetros (Optuna), simulaciones Monte Carlo o pruebas de estrés en las instancias Cloud (Oracle / Azure).
    - El propósito único y prioritario de los nodos cloud es la **Alta Disponibilidad, Baja Latencia y Servicio Web 24/7**. Cualquier tarea de computación intensiva que ponga en riesgo la CPU o RAM de las instancias cloud es considerada una violación a la directiva de estabilidad operativa.

### 2. Centinela Predictivo de Capacidad (quantus-capacity-sentinel.timer):
* Se ejecuta automáticamente cada 30 minutos monitoreando disco, tamaño de BDs y tasa de crecimiento en MB/día.
* **Umbrales de Acción Automatizada**:
  - **< 65% (Normal)**: Operación óptima, registro de telemetría en `/var/log/quantus_capacity_current.json`.
  - **65% a 75% (Aviso Predictivo)**: Alerta preventiva de capacidad en logger del sistema.
  - **75% a 85% (Auto-Offload & Purga)**: Disparo automático de migración vía Tailscale hacia el servidor físico y purga de respaldos locales.
  - **> 85% (Alerta Crítica)**: Notificación de emergencia técnica previa a cualquier bloqueo de servicio.

---

## 🏛️ SECCIÓN 6 — Marco de Licitaciones Públicas, Gestión Documental e Integración CAS-CHILE (SQL Server)

### 1. Principio Rector de Propuestas Técnicas para Licitaciones Públicas (Mercado Público / ChileCompra):
* Toda propuesta técnica elaborada por Antigravity, Codex u OpenCode para licitaciones públicas (ej. `4511-53-LE26` Retiro, `4121-25-LE26` Ninhue) debe estructurarse con rigor metodológico máximo, incorporando:
  1. **Matriz de Cumplimiento Estricta (Compliance Matrix)** mapeando cada cláusula técnica de las bases contra la solución propuesta.
  2. **Arquitectura C4 y Diagramas de Integración**: Contexto, Contenedores, Componentes y Flujos BPMN de visación y firma electrónica (Ley 19.799 FEA/FES).
  3. **Apego Normativo Pleno**: Ley N° 21.180 (Transformación Digital del Estado), Ley N° 19.880 (Bases de los Procedimientos Administrativos), Ley N° 21.719 (Protección de Datos Personales), ISO 27001 / ISO 9001.

### 2. Protocolo de Integración Nativa con CAS-CHILE sobre Microsoft SQL Server On-Premises:
* **Acceso Administrativo Directo**: Aprovechando las credenciales de acceso completo que los municipios poseen sobre sus motores Microsoft SQL Server (Municipalidad, DAEM, Salud), la integración se realiza de forma directa sin intermediación ni cobros abusivos de APIs de CAS-CHILE.
* **Aislamiento en Esquema Staging (`stg_quantus`)**: Jamás alterar esquemas nativos ni triggers de CAS-CHILE. Toda tabla puente, log de auditoría y vista de integración reside en el esquema dedicado `stg_quantus`.
* **Cero Duplicidad e Idempotencia (`MERGE / UPSERT`)**: Clave natural compuesta + Hash SHA-256 para validación de cambios en los 8 subsistemas canónicos:
  a) Gestión Documental
  b) Facturas (DTE / Proveedores)
  c) Correspondencia (Oficina de Partes)
  d) Reportes e Indicadores
  e) Calendario Municipal
  f) Viajes, Vehículos y Cometidos
  g) Trámites en Línea (Portal Ciudadano)
  h) Administración Central y Control de Acceso (RBAC)
* **Aislamiento de Concurrencia**: Consultas de lectura sobre tablas operativas de CAS-CHILE deben ejecutarse obligatoriamente con `WITH (NOLOCK)` o nivel de aislamiento `SNAPSHOT` para impedir bloqueos transaccionales a funcionarios.
* **Garantía para el Acta de Recepción Conforme (Cláusula 9.3.b)**: Pruebas unitarias firmadas, respaldo previo inmutable, trazabilidad transaccional y capacitaciones certificadas para asegurar el 100% de la recepción y liberación de pagos.


---

## 🏢 SECCIÓN 7 — Arquitectura ERP Edge Staging & Continuidad Operativa Oracle-Físico (Auditoría e Implementación ChatGPT)

> [!IMPORTANT]
> **REGLA SUPREMA DE NO INTERFERENCIA OPERATIVA (CARTA MAGNA P67 y P95)**:
> 1. La línea de desarrollo, auditoría y estabilización del núcleo ERP y su arquitectura Edge Staging en Oracle Cloud (`146.181.50.43` / Tailscale `100.108.188.15`) y Azure Cloud (`158.23.185.184`) reside exclusivamente en `/opt/quantus/staging/erp-audit-20260928/`.
> 2. **Queda terminantemente prohibido para Antigravity u otros agentes modificar, sobrescribir, alterar o borrar archivos, bases de datos o servicios dentro de `/opt/quantus/staging/`**, así como manipular configuraciones de Oracle o Azure asociadas a ERP sin instrucción explícita del DRI (Felipe).
> 3. El código de producción corporativo activo (`/opt/quantus/portal/`) se mantiene estrictamente protegido. Ninguna corrección de staging se promueve a producción sin validación integral y autorización humana explícita.

### 1. Componentes del Entorno ERP Edge Staging (ChatGPT · 2026-09-30 / 2026-10-01):
* **Directorio Base de Staging**: `/opt/quantus/staging/erp-audit-20260928/` (en servidor Gateway `100.93.88.89`).
* **Servicios de Staging Dedicados**:
  - `quantus-erp-audit-staging.service`: API del núcleo ERP en staging, escuchando en el puerto interno `127.0.0.1:8095`.
  - `quantus-erp-audit-preview.service`: Portal de vista previa y arnés de pruebas POS en staging, escuchando en el puerto interno `127.0.0.1:8096`.
  - `quantus-edge-mirror-staging.service`: Servicio consumidor de eventos y transacciones en el servidor físico/mirror (`edge-mirror/`).
* **Documentación Canónica de Avances**:
  - `CONTINUIDAD_ORACLE_IMPLEMENTADA_20260930.md`: Arquitectura de continuidad ante desconexión física.
  - `CORRECCIONES_Y_PENDIENTES_20260930.md`: Resolución de 12 hallazgos de auditoría (H01 a H12).
  - `INTEGRACION_POS_Y_ALCANCE.md`: Especificación de adaptadores POS.

### 2. Principios de Continuidad Transaccional y Asimetría de Carga:
* **Escritor Edge en Oracle (`100.108.188.15`)**:
  - Oracle actúa como autoridad de escritura transaccional para ventas, ingresos y operaciones de caja durante caídas o desconexión del servidor físico.
  - Las operaciones y sus eventos pendientes de envío se confirman atómicamente dentro de la **misma transacción PostgreSQL**.
* **Espejo Físico (`edge-mirror`)**:
  - Recibe réplica de eventos por el canal privado de Tailscale. Es idempotente (usa ID y hash SHA-256 de la transacción para evitar doble aplicación).
  - El servidor físico no re-ejecuta ventas ni cobros; únicamente proyecta los estados y conserva la copia maestra inmutable.
* **Prohibición de Tareas Pesadas en Oracle (`physical_processing_required`)**:
  - Procesamiento OCR, importaciones masivas o análisis intensivos son rechazados en Oracle con código `physical_processing_required`, forzando su ejecución exclusiva en el servidor físico On-Premise.
* **Integración de Medios de Pago POS (pos-bridge)**:
  - Módulos en `/opt/quantus/staging/erp-audit-20260928/pos-bridge/` con contratos y adaptadores preparados para Transbank Integrado, Mercado Pago Point y SumUp Solo.
  - Actualmente en modo contrato/interfaz; no realizan llamadas de cobro ni transacciones reales hacia adquirentes en esta fase.


## Memoria estratégica — proyectos y alianzas ERP/Flota (2026-10-07)

Por solicitud expresa de Felipe, conservar y consultar `/opt/quantus/portal/docs/MEMORIA_PROYECTOS_ALIANZAS_ERP_FLOTA.md` al planificar futuros proyectos o alianzas. Incluye ERP–proveedor–Flota con y sin ERP del proveedor, combustible (Copec/Aramco/Enex y regionales), talleres, continuidad operacional, reemplazos, compras agrupadas, maquinaria, conectividad y canales sectoriales. Felipe pide ampliar ideas sin sesgarse a una marca o rubro. El documento distingue propuestas, evidencia y límites; conservarlo no autoriza desarrollo, contacto externo ni anunciar convenios. Las prioridades están pendientes de decisión.

## Actualización de seguridad — 2026-10-25 (prioridad sobre ejemplos SSH anteriores)

- Las contraseñas SSH documentadas previamente fueron revocadas. Root admite SSH únicamente por claves.
- Acceso del propietario desde su Mac: `ssh root@100.93.88.89` y `ssh root@100.117.44.3`; configuración en `~/.ssh/config`, clave `~/.ssh/quantus_ops_20261025`, restringida a su dispositivo Tailscale.
- La conexión gateway → físico conserva su clave operativa existente. No usar sshpass ni desactivar comprobación de host.
- Recuperación de contraseñas PAM/Proxmox: archivo privado del propietario `~/.config/quantus/credentials/server-recovery-20261025.json` (0600). Nunca copiar su contenido a instrucciones, repositorios ni chats.
- Las credenciales SMTP se leen exclusivamente desde archivos de entorno protegidos. Nunca documentar valores de contraseñas de aplicación. Su rotación exige verificación de cuenta Google y comprobación de consumidores antes de revocar la anterior.


## Separación obligatoria de cuentas y proveedores IA — orden de Felipe, 2026-10-25

Esta instrucción tiene prioridad sobre referencias anteriores a modelos o proveedores.

- **Quantus corporativo** (portal, ERP, Flota, Taller, radares, empleos, HSEQ y agentes): únicamente la cuenta Kaggle `felipemejasgonzlez`, notebook `quantus-ia-corporativa-35b`. La inferencia se ejecuta en esa cuenta. Queda prohibido enrutar peticiones corporativas a la API de NVIDIA, a otros proveedores o a la cuenta Kaggle de StratOS.
- **StratOS**: conserva su cuenta Kaggle `felipemejas` y su respaldo NVIDIA. No modificar sus credenciales, router o supervisor como parte de tareas Quantus.
- El control corporativo reside en `/opt/quantus/portal/ai_runtime/kaggle_corporativo/`; credenciales exclusivamente en `/etc/quantus-ai/kaggle-corporativo/`; estado en `/var/lib/quantus-ai/kaggle-corporativo/`. Endpoint privado estable: `http://100.117.44.3:18410/v1`. Ningún servicio depende del Mac o de Chrome.
- Usar siempre `KAGGLE_API_TOKEN=/etc/quantus-ai/kaggle-corporativo/access_token` en el CLI corporativo. `KAGGLE_CONFIG_DIR` por sí solo no aísla los access tokens del SDK; nunca sobrescribir ni reutilizar `~/.kaggle/access_token` o `/etc/stratos/` para Quantus.
- El router corporativo valida dominio, cuenta, modelo, sesión y vigencia antes de publicar. Si Kaggle no está disponible, informa recuperación y reintento; nunca cambia de cuenta/proveedor ni fabrica una respuesta exitosa. Cada módulo conserva sus permisos, identidad de clientes y validación de herramientas en el servidor.
- Memoria operativa y evidencia: `/opt/quantus/portal/ai_runtime/kaggle_corporativo/README.md`. Los nombres históricos de herramientas o de pesos abiertos no autorizan llamadas a proveedores externos.

---

## 🏛️ SECCIÓN 8 — Estándar Institucional Canónico de Entregables de Licitaciones Mercado Público

> [!IMPORTANT]
> **REGLA SUPREMA DE ENTREGABLES DE LICITACIONES**:
> Todo proceso licitatorio abordado por Quantus Chile SpA debe culminar obligatoriamente en la carpeta `01_LISTAS_PARA_REVISION/{CODIGO}/08_ENTREGA_FINAL_SIN_GUIONES_BAJOS/` bajo la tríada documental limpia (sin guiones bajos), con la paleta visual `#002B49`, `logo_oficial_quantus.png`, `firma_felipe_mejias.png` y representación legal de Felipe Esteban Mejías González (RUT 14.011.762-5):
> 1. `01 Propuesta Tecnica Oficial Quantus Chile SpA.docx`
> 2. `02 Oferta Economica Oficial Quantus Chile SpA.docx`
> 3. `03 Anexos Administrativos y Declaraciones Quantus Chile SpA.docx`
> 
> * **Memoria de Referencia (Expedientes de Oro)**: Ante cualquier duda de formato o redacción, consultar y calcar `1108660-10-LE26` y `1057503-146-LE26`.
> * **Compilación Determinista**: Los agentes no escriben XML a mano; el motor `generar_entregables_finales.py` o `sistema_licitaciones/documentos.py` compila los datos generados por los especialistas.
> * **Sub-Carta de Módulo**: La gobernanza detallada de licitaciones reside en `quantus/licitaciones/AGENTS.md`.

---

## 🤖 SECCIÓN 9 — Sistema Canónico de Agentes Autónomos, Router y Catálogo Visual de Productos

> [!CRITICAL]
> **OBLIGACIÓN PARA TODA INTELIGENCIA ARTIFICIAL (Antigravity, Hermes, OpenCode, Codex, Claude, ChatGPT)**:
> 1. **Dónde están los agentes**:
>    - Registro y balanceador: `quantus/infraestructura/quantus_model_router.py` (`AGENT_ROSTER` con los roles de 1ª, 2ª y 3ª línea de defensa).
>    - Cadena de deliberación autónoma: `quantus/marketing/ejecutar_cadena_cio_marketing.py` (CEO -> CIO-ORCHESTRATOR -> MEDIA-GROWTH -> CIO Auditoría -> CEO).
>    - Registro de conversación inter-agentes: `quantus_radar_prospector/social_intelligence.db` (tabla `agentes_conversacion`).
> 2. **Qué es lo que se formó**:
>    - **Catálogo Canónico Oficial de Productos**: `quantus/marketing/rag/CATALOGO_OFICIAL_PRODUCTOS.md`. Especificación técnica estricta de los 8 productos de Quantus. Cero invención.
>    - **Galería Oficial de Evidencia Visual**: `quantus/marketing/rag/catalogo_visual/` con las 7 capturas de pantallas reales de UI (`screen_caja_pos.png`, `screen_inventario.png`, `screen_analytics.png`, `screen_ingresos.png`, `screen_resumen.png`, `pos_preview_touch.png`, `screen_radar_diario_oficial.png`).
>    - **Inyección Automática en Inferencia**: En `quantus_model_router.py`, todo llamado a agentes comerciales/operativos recibe automáticamente el catálogo y la evidencia visual.
> 3. **Prohibición Inviolable (Carta Magna P0 & Regla 9)**:
>    - Quantus Chile SpA vende **SOFTWARE EN LA NUBE E INTELIGENCIA DE DATOS**, NO hardware físico.
>    - Queda estrictamente prohibido a cualquier IA generar guiones, imágenes o videos con máquinas POS físicas o impresoras con marca Quantus.
>    - Todo contenido audiovisual o de marketing debe basarse exclusivamente en las pantallas reales de `quantus/marketing/rag/catalogo_visual/`.
>    - Documento maestro de consulta: `SISTEMA_AGENTES_Y_CATALOGO_VISUAL.md`.

