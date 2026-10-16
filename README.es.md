[Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# Calculadora XP para Ubuntu

Calculadora de escritorio con aspecto clásico, menús en portugués y modos estándar y científico. Implementación independiente en Python y GTK 4.

Desarrollada con [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) como apoyo para investigar el ejecutable original y con la ayuda de **OpenAI Codex**, utilizando el modelo **GPT 6.1 Sol**, para la implementación, las pruebas y el empaquetado para Ubuntu.

## Instalación

```sh
sudo apt install ./calc-xp_1.0.0_all.deb
calc-xp
```

La aplicación también aparece como **Calculadora XP** en el menú de aplicaciones. Dependencias: `python3` (3.10 o posterior), `python3-gi` y `gir1.2-gtk-4.0`. Arquitectura del paquete: `all`.

## Funciones

- El modo estándar calcula las operaciones en el orden introducido; el científico respeta la precedencia y los paréntesis.
- Memoria MC, MR, MS y M+, porcentajes, potencias, raíces y funciones trigonométricas.
- Funciones inversas e hiperbólicas, conversiones decimal/hexadecimal/octal/binario y operaciones de bits.
- Media, suma y desviación estándar, con una lista de datos estadísticos.
- Copiar y pegar números, agrupación de miles e iconos de 16, 32 y 48 píxeles.

## Atajos de teclado

| Tecla | Acción |
|---|---|
| Enter o `=` | Calcular |
| Esc | Borrar |
| Delete | Borrar la entrada |
| Backspace | Borrar un carácter |
| F9 | Cambiar el signo |
| Ctrl+C / Ctrl+V | Copiar / pegar un número |
| F5 / F6 / F7 / F8 | Hexadecimal / decimal / octal / binario |
| F2 / F3 / F4 | Grados / radianes / grados centesimales, o tamaño de palabra en las bases enteras |

**Exibir → Padrão / Científica** permite cambiar de modo. Inv activa las funciones inversas; Hyp activa las hiperbólicas. Dat añade datos estadísticos y Sta abre la lista. La ayuda local está disponible con F1. La interfaz está en portugués y la pantalla utiliza la coma decimal.

Las preferencias se guardan en `~/.config/calc-xp/settings.json`, respetando `XDG_CONFIG_HOME`. La memoria y los datos estadísticos se conservan durante la sesión. La aritmética utiliza hasta 32 dígitos; la trigonometría, aproximadamente 15. No se garantiza que todos los redondeos y límites coincidan con los de la calculadora clásica.

## Desarrollo

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0 git
python3 -m unittest discover -s tests -v
python3 -m calc_xp.app
```

Prueba gráfica opcional, en una sesión gráfica:

```sh
CALC_XP_SCREENSHOTS=dist/screenshots python3 -m calc_xp.app --smoke-test
```

La prueba de regresión de los menús cambia de modo ocho veces y comprueba que los menús se vuelvan a abrir y que los cálculos funcionen después de cada cambio:

```sh
GDK_BACKEND=x11 GSK_RENDERER=cairo python3 tests/menu_regression.py
# Para probar con eventos del puntero, instale xdotool y añada --pointer.
```

## Empaquetado

```sh
python3 packaging/build_deb.py
# Genera el paquete, los fuentes y las sumas de verificación desde el índice de Git:
python3 packaging/build_release.py
```

Los resultados se guardan en `dist/`. La compilación para publicación utiliza una copia limpia de los archivos fuente seleccionados en Git. Los archivos ignorados quedan fuera del paquete y del archivo de fuentes.

Después de instalar el paquete, `python3 packaging/verify_installed.py` comprueba su integridad, los archivos instalados, los iconos y el acceso del menú de aplicaciones.

## Licencia y créditos

El código independiente se distribuye bajo la licencia [MIT](LICENSE). El icono original de la Calculadora de Windows XP es un recurso gráfico de Microsoft, identificado por separado en [NOTICE.md](packaging/icons/NOTICE.md); no está cubierto por la licencia MIT de este proyecto. El proyecto no está afiliado a Microsoft.
