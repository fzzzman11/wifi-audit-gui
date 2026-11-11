# Aviso legal y ético · WiFi Audit Lab

> **WiFi Audit Lab es software exclusivamente educativo.** Está desarrollado
> como proyecto académico para un laboratorio universitario de ciberseguridad
> y solo puede utilizarse sobre redes inalámbricas **propias o autorizadas**.
> Cualquier otro uso queda expresamente fuera del propósito del proyecto.

---

## 1. Naturaleza del proyecto

WiFi Audit Lab es un trabajo de laboratorio universitario que envuelve en una
interfaz gráfica (PyQt6) el flujo didáctico clásico de auditoría WPA/WPA2
descrito en la documentación oficial de la suite **aircrack-ng**:

| Fase | Herramienta | Acción |
|------|-------------|--------|
| 1 | `airmon-ng` | Coloca el adaptador en modo monitor |
| 2 | `airodump-ng` | Escanea y enumera redes cercanas |
| 3 | `airodump-ng` + `aireplay-ng` | Captura dirigida del handshake; el envío de paquetes de desautenticación (*deauth*) es **opcional** y requiere confirmación explícita del usuario |
| 4 | `aircrack-ng` | Prueba un diccionario de contraseñas contra el handshake capturado |

No se implementa ninguna técnica novedosa ni encubierta: todo lo que hace la
aplicación es equivalente a ejecutar manualmente esas herramientas desde una
terminal. El objetivo es didáctico: observar, de forma guiada, por qué WPA/WPA2
con contraseñas débiles es vulnerable a ataques de diccionario.

## 2. Condiciones de uso

El software únicamente puede emplearse en:

- Redes WiFi de **tu propiedad** (por ejemplo, el router de pruebas del
  laboratorio).
- Redes del **laboratorio universitario** asignadas para la práctica.
- Redes de terceros **con autorización expresa, escrita y verificable** del
  propietario, definiendo el alcance (BSSID objetivo, canales y horario).
- Entornos de pruebas aislados configurados para la docencia.

**Queda prohibido** cualquier uso contra redes de terceros sin autorización,
incluido el "mero escaneo", la captura de handshakes de vecinos, el envío de
paquetes de desautenticación a redes ajenas o la publicación de capturas
obtenidas de esa forma.

## 3. Marco legal

El acceso no autorizado a sistemas y redes informáticas, la interceptación de
comunicaciones y la perturbación del funcionamiento de servicios constituyen
**delito en la mayoría de jurisdicciones**, con penas que pueden incluir
prisión y multas, además de responsabilidad civil. Ejemplos ilustrativos
(**lista no exhaustiva**; consulta siempre tu legislación local):

- **España**: arts. 197–198 del Código Penal (descubrimiento y revelación de
  secretos, acceso ilegal a sistemas y datos informáticos, interceptación de
  comunicaciones) y arts. 264 y ss. (sabotaje informático).
- **Estados Unidos**: Computer Fraud and Abuse Act (18 U.S.C. § 1030).
- **Reino Unido**: Computer Misuse Act 1990.
- **Marco internacional**: Convenio de Budapest sobre Ciberdelincidencia y sus
  transposiciones nacionales.

El hecho de que el software esté disponible públicamente, de que el diálogo de
inicio solicite una confirmación o de que exista este documento **no constituye
autorización ni exime de responsabilidad** al usuario.

## 4. Transparencia técnica y datos sensibles

- Los archivos `.cap` generados (por defecto en `~/wifi_audit_capturas/`)
  contienen el *handshake* WPA/WPA2, es decir, **material de autenticación**
  de la red auditada. Trátalos como si fueran contraseñas:
  - No los subas a repositorios ni servicios públicos (el `.gitignore` del
    proyecto los excluye expresamente).
  - No los compartas sin autorización.
  - Elimínalos al terminar la práctica (`rm -rf ~/wifi_audit_capturas`).
- El envío de paquetes de *deauth* interrumpe la conectividad de los clientes
  legítimos de la red: úsalo solo en redes de pruebas.
- Los CSV de `airodump-ng` contienen un inventario de redes y clientes
  cercanos (datos personales): anonimízalos antes de usarlos en el informe.

## 5. Buenas prácticas de laboratorio recomendadas

1. **Infraestructura dedicada**: router propio del laboratorio con una
   contraseña de prueba elegida por el profesor, y un cliente desechable.
2. **Documenta la autorización** antes de empezar: quién autoriza, qué red
   (BSSID), en qué horario y con qué alcance.
3. **Genera el handshake de forma natural** conectando y desconectando un
   cliente antes de recurrir al *deauth*.
4. **Presenta resultados anonimizados**: difumina BSSIDs y SSIDs de terceros
   que aparezcan por accidente en las capturas de pantalla del informe.
5. **Restaura siempre** la interfaz a modo *managed* y reinicia
   NetworkManager al terminar (la aplicación lo hace automáticamente al
   cerrarse, pero verifícalo).

## 6. Ausencia de garantía y limitación de responsabilidad

Este software se proporciona "tal cual", **sin garantía de ningún tipo**,
expresa o implícita, incluyendo sin limitación las garantías de
comercialización o idoneidad para un propósito particular. El autor o autores
del proyecto y la institución académica asociada **no se hacen responsables**
de ningún daño directo o indirecto, pérdida de datos, pérdida de servicio ni
de cualquier uso ilícito que terceros hagan de este software.

**El único responsable del uso de esta herramienta es el usuario final.**

## 7. Contacto

Para dudas sobre el uso docente del proyecto, el alcance de las prácticas o la
autorización de redes del laboratorio, contacta con el equipo docente:

- Autor: `[nombre del alumno] · [correo de la universidad]`
- Asignatura: `[nombre de la asignatura] · [universidad]`

---

*WiFi Audit Lab · proyecto académico de ciberseguridad · curso 2025/2026.*
