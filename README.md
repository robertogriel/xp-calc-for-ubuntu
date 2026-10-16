[Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# Calculadora XP para Ubuntu

Calculadora de desktop com visual clássico, menus em português e modos padrão e científico. Implementação independente em Python e GTK 4.

Desenvolvido com o [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) no apoio à investigação do executável original e com o auxílio do **OpenAI Codex**, usando o modelo **GPT 6.1 Sol**, na implementação, nos testes e no empacotamento para Ubuntu.

## Instalação

```sh
sudo apt install ./calc-xp_1.0.0_all.deb
calc-xp
```

O aplicativo também aparece como **Calculadora XP** no menu de aplicativos. Dependências: `python3` (3.10 ou posterior), `python3-gi` e `gir1.2-gtk-4.0`. Pacote de arquitetura `all`.

## Recursos

- Modo padrão com operações na ordem digitada; modo científico com precedência e parênteses.
- Memória MC, MR, MS e M+, porcentagem, potências, raízes e funções trigonométricas.
- Funções inversas e hiperbólicas, conversões decimal/hexadecimal/octal/binário e operações bit a bit.
- Média, soma e desvio padrão, com lista de dados estatísticos.
- Copiar e colar números, agrupamento de milhares e ícones nas resoluções de 16, 32 e 48 pixels.

## Atalhos

| Tecla | Ação |
|---|---|
| Enter ou `=` | Calcular |
| Esc | Limpar |
| Delete | Limpar entrada |
| Backspace | Apagar um caractere |
| F9 | Trocar sinal |
| Ctrl+C / Ctrl+V | Copiar / colar um número |
| F5 / F6 / F7 / F8 | Hexadecimal / decimal / octal / binário |
| F2 / F3 / F4 | Graus / radianos / grados, ou largura da palavra nas bases inteiras |

**Exibir → Padrão / Científica** alterna os modos. Inv ativa funções inversas; Hyp ativa funções hiperbólicas. Dat adiciona dados estatísticos e Sta abre a lista. A ajuda local está disponível em F1.

Preferências: `~/.config/calc-xp/settings.json`, respeitando `XDG_CONFIG_HOME`. Memória e estatísticas duram durante a execução. Aritmética com até 32 algarismos; trigonometria com aproximadamente 15. Não se garante igualdade de todos os arredondamentos e limites da calculadora clássica.

## Desenvolvimento

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0 git
python3 -m unittest discover -s tests -v
python3 -m calc_xp.app
```

Teste gráfico opcional, em uma sessão gráfica:

```sh
CALC_XP_SCREENSHOTS=dist/screenshots python3 -m calc_xp.app --smoke-test
```

O teste de regressão dos menus executa oito trocas de modo e confirma a reabertura dos menus e o cálculo após cada troca:

```sh
GDK_BACKEND=x11 GSK_RENDERER=cairo python3 tests/menu_regression.py
# Para testar com eventos de ponteiro, instale xdotool e adicione --pointer.
```

## Empacotamento

```sh
python3 packaging/build_deb.py
# Gera pacote, fontes e checksums a partir dos arquivos do índice Git:
python3 packaging/build_release.py
```

Os resultados ficam em `dist/`. O empacotamento da versão para publicação compila a partir de uma cópia limpa dos fontes selecionados no Git. Arquivos ignorados não participam do pacote nem do arquivo de fontes.

Após instalar o pacote, `python3 packaging/verify_installed.py` verifica sua integridade, os arquivos instalados, os ícones e o atalho.

## Licença e créditos

O código independente está sob a licença [MIT](LICENSE). O ícone original da Calculadora do Windows XP é um recurso gráfico da Microsoft, identificado separadamente em [NOTICE.md](packaging/icons/NOTICE.md); ele não está coberto pela licença MIT deste projeto. O projeto não é afiliado à Microsoft.
