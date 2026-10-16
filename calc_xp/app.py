#!/usr/bin/python3
"""GTK desktop reconstruction inspired by the Windows XP Calculator."""
import json
import os
from pathlib import Path
import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Graphene', '1.0')
from gi.repository import Gtk, Gdk, Gio, GLib, Graphene

try:
    from .engine import Calculator
    from .version import VERSION
except ImportError:
    from engine import Calculator
    from version import VERSION


CSS = b'''
window.calc { background: #ece9d8; color: #111; font-family: Arial, "Liberation Sans", sans-serif; font-size: 13px; }
.calc .client { background: #ece9d8; color: #111; }
.calc button { min-height: 26px; min-width: 32px; padding: 1px 5px; border-radius: 2px;
  background: linear-gradient(#ffffff, #f5f5f2); border: 1px solid #aaa99e;
  box-shadow: inset 1px 1px #fff, 1px 1px #d2d0c3; color: #0000ee; font-weight: normal; }
.calc button:hover { border-color: #316ac5; background: #fff9df; }
.calc button:active, .calc button:checked { background: #dedcca; box-shadow: inset 1px 1px #9b998c; }
.calc button:focus-visible { outline: 1px dotted #111; outline-offset: -4px; }
.calc button.red { color: #e00000; }
.calc button.magenta { color: #c000c0; }
.calc button:disabled { color: #99978e; background: #e6e4da; }
.calc .menubar { background: #f4f3eb; padding: 0; }
.calc .menubar button { color: #111; background: transparent; border: 0; box-shadow: none;
  min-width: 0; min-height: 19px; padding: 1px 7px; }
.calc .menubar arrow { min-width: 0; min-height: 0; opacity: 0; }
.calc .display { background: white; color: #000; border: 1px solid #8e8c7e;
  box-shadow: inset 1px 1px #c5c3b5; padding: 6px 7px; font-family: "DejaVu Sans Mono", monospace;
  font-size: 19px; min-height: 29px; }
.calc .indicator { background: #ece9d8; border: 1px solid #aaa99e; min-width: 29px;
  min-height: 25px; box-shadow: inset 1px 1px #fff; font-size: 12px; }
.calc checkbutton { font-size: 12px; padding: 0; min-height: 22px; }
.calc checkbutton label { color: #111; }
.calc .selector { border: 1px solid #d5d2c5; padding: 3px; }
.calc popover contents { background: #f4f3eb; color: #111; }
.calc popover button { color: #111; min-height: 24px; }
.calc .status { font-size: 11px; color: #59574e; padding: 2px; }
'''


class CalcWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Calculadora XP')
        self.set_icon_name('calc-xp')
        self.add_css_class('calc')
        self.set_resizable(False)
        self.engine = Calculator()
        self.grouping = False
        self.config_path = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'calc-xp' / 'settings.json'
        self.read_settings()
        self.buttons = {}
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.root.add_css_class('client')
        self.set_child(self.root)
        self.create_menu()
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        for prop in ('margin_start', 'margin_end', 'margin_top', 'margin_bottom'):
            getattr(self.body, 'set_' + prop)(8)
        self.root.append(self.body)
        self.screen = Gtk.Label(xalign=1, selectable=True, single_line_mode=True)
        self.screen.add_css_class('display')
        self.screen.set_hexpand(True)
        self.screen.set_tooltip_text('Resultado — Ctrl+C para copiar, Ctrl+V para colar um número')
        self.body.append(self.screen)
        self.panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.body.append(self.panel)
        controller = Gtk.EventControllerKey()
        controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        controller.connect('key-pressed', self.on_key)
        self.add_controller(controller)
        self.connect('close-request', self.on_close)
        self.rebuild()

    def read_settings(self):
        try:
            settings = json.loads(self.config_path.read_text())
            if settings.get('mode') in ('standard', 'scientific'):
                self.engine.mode = settings['mode']
            if settings.get('angle') in ('deg', 'rad', 'grad'):
                self.engine.angle = settings['angle']
            self.grouping = bool(settings.get('grouping', False))
        except (OSError, ValueError, TypeError):
            pass

    def on_close(self, *_):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps({'mode': self.engine.mode,
                'angle': self.engine.angle, 'grouping': self.grouping}))
        except OSError:
            pass
        return False

    def create_menu(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bar.add_css_class('menubar')
        self.root.append(bar)
        for label, items in [
            ('Editar', [('Copiar        Ctrl+C', self.copy), ('Colar          Ctrl+V', self.paste)]),
            ('Exibir', [('Padrão', lambda: self.set_mode('standard')),
                       ('Científica', lambda: self.set_mode('scientific')),
                       ('Agrupar dígitos', self.toggle_grouping)]),
            ('Ajuda', [('Como usar          F1', self.help), ('Sobre a Calculadora XP', self.about)])]:
            menu = Gtk.MenuButton(label=label)
            popover = Gtk.Popover()
            popover._pending_action = None
            popover.connect('unmap', self.menu_unmapped)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            for text, callback in items:
                button = Gtk.Button(label=text)
                button.connect('clicked', self.activate_menu_item, menu, callback)
                box.append(button)
            popover.set_child(box)
            menu.set_popover(popover)
            bar.append(menu)

    def activate_menu_item(self, _button, menu, callback):
        popover = menu.get_popover()
        popover._pending_action = callback
        menu.popdown()
        if not popover.get_mapped():
            self.menu_unmapped(popover)

    def menu_unmapped(self, popover):
        callback = popover._pending_action
        popover._pending_action = None
        if callback is not None:
            # Let GTK release the popup surface and its input grab before resizing.
            def run_action():
                callback()
                return GLib.SOURCE_REMOVE
            GLib.idle_add(run_action)

    def make_button(self, text, key=None, color=None, width=None):
        key = text if key is None else key
        button = Gtk.Button(label=text)
        button.set_hexpand(True)
        if color: button.add_css_class(color)
        if width: button.set_size_request(width, -1)
        button.set_tooltip_text({'sqrt': 'Raiz quadrada', 'reciprocal': 'Inverso (1/x)',
            'pow': 'Potência x elevado a y', 'Dat': 'Adicionar o valor aos dados estatísticos',
            'Sta': 'Exibir e editar os dados estatísticos', 'dms': 'Graus, minutos e segundos; Inv para converter de volta',
            'F-E': 'Alternar notação científica', 'Exp': 'Digitar o expoente de uma potência de 10',
            'MC': 'Limpar memória', 'MR': 'Recuperar memória', 'MS': 'Guardar na memória',
            'M+': 'Somar à memória', 'stddev': 'Desvio padrão amostral; Inv para populacional'}.get(key, text))
        button.connect('clicked', lambda _b: self.action(key))
        self.buttons[key] = button
        return button

    def rebuild(self):
        while child := self.panel.get_first_child(): self.panel.remove(child)
        self.buttons = {}
        science = self.engine.mode == 'scientific'
        if science:
            selectors = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.base_radios = {}
            group = None
            bases = Gtk.Box(spacing=8); bases.add_css_class('selector')
            for text, base in [('Hex', 16), ('Dec', 10), ('Oct', 8), ('Bin', 2)]:
                radio = Gtk.CheckButton(label=text)
                if group: radio.set_group(group)
                else: group = radio
                radio.set_active(self.engine.base == base)
                radio.connect('toggled', lambda b, n=base: self.select_base(n) if b.get_active() else None)
                self.base_radios[base] = radio
                bases.append(radio)
            selectors.append(bases)
            angles = Gtk.Box(spacing=8); angles.add_css_class('selector'); angles.set_hexpand(True)
            group = None
            choices = [('Graus', 'deg'), ('Radianos', 'rad'), ('Grados', 'grad')] if self.engine.base == 10 else [('Qword', 64), ('Dword', 32), ('Word', 16), ('Byte', 8)]
            for text, value in choices:
                radio = Gtk.CheckButton(label=text)
                if group: radio.set_group(group)
                else: group = radio
                radio.set_active(value == (self.engine.angle if self.engine.base == 10 else self.engine.bits))
                radio.connect('toggled', self.select_unit, value)
                angles.append(radio)
            selectors.append(angles)
            self.panel.append(selectors)
        top = Gtk.Box(spacing=7)
        if science:
            self.inv = Gtk.CheckButton(label='Inv'); self.inv.set_active(self.engine.inverse)
            self.inv.connect('toggled', lambda b: setattr(self.engine, 'inverse', b.get_active()))
            self.hyp = Gtk.CheckButton(label='Hyp'); self.hyp.set_active(self.engine.hyperbolic)
            self.hyp.connect('toggled', lambda b: setattr(self.engine, 'hyperbolic', b.get_active()))
            top.append(self.inv); top.append(self.hyp)
        self.memory_indicator = Gtk.Label()
        self.memory_indicator.add_css_class('indicator')
        top.append(self.memory_indicator)
        if science:
            self.paren_indicator = Gtk.Label(); self.paren_indicator.add_css_class('indicator')
            top.append(self.paren_indicator)
        spacer = Gtk.Box(); spacer.set_hexpand(True); top.append(spacer)
        for text in ('Backspace', 'CE', 'C'):
            top.append(self.make_button(text, 'clear' if text == 'C' else text, 'red', 65 if text == 'Backspace' else 52))
        self.panel.append(top)
        grid = Gtk.Grid(column_spacing=7, row_spacing=7)
        self.panel.append(grid)
        if science:
            layout = [
                [('Sta', 'Sta'), ('F-E','F-E'), ('(','('), (')',')'), ('MC','MC'), ('7','7'), ('8','8'), ('9','9'), ('/','/'), ('Mod','mod'), ('And','and')],
                [('Ave','average'), ('dms','dms'), ('Exp','Exp'), ('ln','ln'), ('MR','MR'), ('4','4'), ('5','5'), ('6','6'), ('*','*'), ('Or','or'), ('Xor','xor')],
                [('Sum','sum'), ('sin','sin'), ('x^y','pow'), ('log','log'), ('MS','MS'), ('1','1'), ('2','2'), ('3','3'), ('-','-'), ('Lsh','lsh'), ('Not','not')],
                [('s','stddev'), ('cos','cos'), ('x^3','cube'), ('n!','factorial'), ('M+','M+'), ('0','0'), ('+/-','+/-'), ('.','.'), ('+','+'), ('=','='), ('Int','int')],
                [('Dat','Dat'), ('tan','tan'), ('x^2','square'), ('1/x','reciprocal'), ('pi','pi'), ('A','digit:A'), ('B','digit:B'), ('C','digit:C'), ('D','digit:D'), ('E','digit:E'), ('F','digit:F')]]
        else:
            layout = [[(t,t) for t in row] for row in [
                ['MC','7','8','9','/','sqrt'], ['MR','4','5','6','*','%'],
                ['MS','1','2','3','-','reciprocal'], ['M+','0','+/-','.','+','=']]]
        for y, row in enumerate(layout):
            for x, (text, key) in enumerate(row):
                label = {'sqrt':'sqrt', 'reciprocal':'1/x'}.get(text,text)
                color = 'red' if key in ('MC','MR','MS','M+','+','-','*','/','=') else 'magenta' if science and x in (1,2,3) else None
                button = self.make_button(label,key,color,40 if science else 43)
                grid.attach(button,x,y,1,1)
        self.screen.set_size_request(590 if science else 330, -1)
        self.set_default_size(1,1)
        self.refresh()

    def select_unit(self, button, value):
        if not button.get_active(): return
        if isinstance(value, int):
            number = self.engine.number()
            self.engine.bits = value
            self.engine.put(number)
        else: self.engine.angle = value
        self.refresh()

    def select_base(self, base):
        if self.engine.error: self.engine.clear()
        self.engine.change_base(base)
        self.rebuild()

    def set_mode(self, mode):
        self.engine.set_mode(mode)
        self.rebuild()

    def toggle_grouping(self):
        self.grouping = not self.grouping
        self.refresh()

    def action(self, key):
        if key == 'Sta': self.show_statistics(); return
        self.engine.press(key)
        self.refresh()

    def refresh(self):
        self.screen.set_text(self.engine.display(self.grouping))
        self.screen.set_tooltip_text(self.engine.display(self.grouping))
        self.memory_indicator.set_text('M' if self.engine.memory else '')
        if self.engine.mode == 'scientific':
            self.paren_indicator.set_text(str(self.engine.operators.count('(')) if '(' in self.engine.operators else '')
            for key, button in self.buttons.items():
                if key.startswith('digit:') or key in '0123456789':
                    digit = key[6:] if key.startswith('digit:') else key
                    button.set_sensitive(int(digit,16) < self.engine.base)
                elif key in ('.','sin','cos','tan','ln','log','factorial','dms','Exp','pi','F-E'):
                    button.set_sensitive(self.engine.base == 10)

    def copy(self):
        text = self.engine.entry if self.engine.base != 10 else str(self.engine.number()) if not self.engine.error else self.engine.error
        self.get_clipboard().set(text)

    def paste(self):
        def received(clipboard, result):
            try:
                text = clipboard.read_text_finish(result)
                if text: self.engine.paste(text)
            except (GLib.Error, ValueError, ArithmeticError) as exc:
                self.message('Não foi possível colar', str(exc))
            self.refresh()
        self.get_clipboard().read_text_async(None, received)

    def message(self, title, text):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, text=title,
            secondary_text=text, buttons=Gtk.ButtonsType.CLOSE)
        dialog.connect('response', lambda d, _r: d.destroy())
        dialog.present()

    def help(self):
        self.message('Como usar', 'Padrão: operações na ordem digitada. Científica: precedência e parênteses.\n\n'
            'Teclado: números e + − * /; Enter ou = calcula; Esc limpa; Delete limpa a entrada; Backspace apaga; '
            'F9 troca o sinal; @ calcula a raiz; % calcula a porcentagem no modo padrão.\n\n'
            'Científica: F5 Hex, F6 Dec, F7 Oct, F8 Bin; F2/F3/F4 selecionam a unidade angular '
            '(ou Dword/Word/Byte). Inv ativa funções inversas e Hyp as hiperbólicas.\n\n'
            'Estatística: Dat inclui o visor; Sta abre os dados; Ave calcula a média; Sum a soma; s o desvio padrão. '
            'Inv+Sum soma os quadrados e Inv+s calcula o desvio populacional.\n\n'
            'Ctrl+C copia e Ctrl+V cola um número. MS guarda, MR recupera, M+ soma e MC limpa a memória.')

    def about(self):
        self.message(f'Calculadora XP {VERSION}', 'Implementação independente para Ubuntu, inspirada na calculadora clássica do Windows XP.\n\n'
            'Python 3 + GTK 4. Aritmética decimal de até 32 algarismos; trigonometria com aproximadamente 15 algarismos. '
            'Ícone original extraído do calc.exe fornecido. Código da calculadora implementado independentemente.')

    def show_statistics(self):
        window = Gtk.Window(title='Dados estatísticos', transient_for=self, modal=False)
        window.add_css_class('calc'); window.set_default_size(300,320)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for prop in ('margin_start','margin_end','margin_top','margin_bottom'): getattr(box,'set_'+prop)(10)
        listing = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        scroller = Gtk.ScrolledWindow(vexpand=True); scroller.set_child(listing); box.append(scroller)
        def reload():
            while child := listing.get_first_child(): listing.remove(child)
            for number in self.engine.statistics:
                listing.append(Gtk.Label(label=str(number), xalign=1, margin_end=5, margin_top=4, margin_bottom=4))
        def remove(_b):
            row = listing.get_selected_row()
            if row: self.engine.statistics.pop(row.get_index()); reload()
        def clear(_b): self.engine.statistics.clear(); reload()
        def load(_b):
            row = listing.get_selected_row()
            if row: self.engine.put(self.engine.statistics[row.get_index()]); self.refresh()
        buttons = Gtk.Box(spacing=5)
        for label, callback in [('Carregar',load), ('Excluir',remove), ('Limpar',clear)]:
            button = Gtk.Button(label=label); button.connect('clicked',callback); buttons.append(button)
        box.append(buttons); window.set_child(box); reload(); window.present()

    def on_key(self, _controller, keyval, _code, state):
        name = Gdk.keyval_name(keyval)
        if state & Gdk.ModifierType.CONTROL_MASK:
            if name.lower() == 'c': self.copy(); return True
            if name.lower() == 'v': self.paste(); return True
            if name.lower() in ('l','r','m','p'):
                self.action({'l':'MC','r':'MR','m':'MS','p':'M+'}[name.lower()]); return True
            return False
        if name == 'F1': self.help(); return True
        if self.engine.mode == 'scientific':
            if name in ('F5','F6','F7','F8'):
                self.select_base({'F5':16,'F6':10,'F7':8,'F8':2}[name]); return True
            if name in ('F2','F3','F4'):
                if self.engine.base == 10: self.engine.angle = {'F2':'deg','F3':'rad','F4':'grad'}[name]
                else:
                    number = self.engine.number(); self.engine.bits = {'F2':32,'F3':16,'F4':8}[name]; self.engine.put(number)
                self.rebuild(); return True
        key = {'Return':'=', 'KP_Enter':'=', 'Escape':'clear', 'Delete':'CE', 'F9':'+/-',
            'BackSpace':'Backspace', 'period':'.', 'comma':'.', 'KP_Decimal':'.', 'KP_Separator':'.',
            'plus':'+', 'KP_Add':'+', 'minus':'-', 'KP_Subtract':'-', 'asterisk':'*', 'KP_Multiply':'*',
            'slash':'/', 'KP_Divide':'/', 'equal':'=', 'percent':'%', 'parenleft':'(', 'parenright':')', 'at':'sqrt'}.get(name)
        if name.startswith('KP_') and name[3:].isdigit(): key = name[3:]
        if len(name) == 1 and name.isdigit(): key = name
        if len(name) == 1 and name.upper() in 'ABCDEF' and self.engine.base == 16: key = 'digit:' + name.upper()
        if key:
            self.action(key); return True
        return False


class App(Gtk.Application):
    def __init__(self):
        GLib.set_prgname('calc-xp')
        GLib.set_application_name('Calculadora XP')
        super().__init__(application_id='io.github.calcxp.Calculator', flags=Gio.ApplicationFlags.NON_UNIQUE)

    def do_activate(self):
        provider = Gtk.CssProvider(); provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window = CalcWindow(self)
        self.window.present()
        if '--smoke-test' in sys.argv:
            GLib.timeout_add(700, self.smoke_test)

    def smoke_test(self):
        try:
            w = self.window
            w.set_mode('standard')
            for k in ('2','+','3','*','4','='): w.buttons[k].emit('clicked')
            assert w.engine.number() == 20
            GLib.timeout_add(400, self.smoke_scientific)
        except Exception:
            import traceback; traceback.print_exc(); self.quit(); self.smoke_failed = True
        return False

    def smoke_scientific(self):
        try:
            self.capture('ubuntu-standard.png')
            w = self.window
            w.set_mode('scientific')
            for k in ('2','+','3','*','4','='): w.buttons[k].emit('clicked')
            assert w.engine.number() == 14
            GLib.timeout_add(500, self.finish_smoke)
        except Exception:
            import traceback; traceback.print_exc(); self.quit(); self.smoke_failed = True
        return False

    def capture(self, filename):
        directory = Path(os.environ.get('CALC_XP_SCREENSHOTS', '.'))
        directory.mkdir(parents=True, exist_ok=True)
        widget = self.window.root
        paintable = Gtk.WidgetPaintable.new(widget)
        snapshot = Gtk.Snapshot()
        paintable.snapshot(snapshot, widget.get_width(), widget.get_height())
        node = snapshot.to_node()
        rect = Graphene.Rect(); rect.init(0,0,widget.get_width(),widget.get_height())
        texture = self.window.get_native().get_renderer().render_texture(node, rect)
        texture.save_to_png(str(directory / filename))

    def finish_smoke(self):
        try:
            self.capture('ubuntu-scientific.png')
            self.window.select_base(16)
            self.window.action('digit:F'); self.window.action('and'); self.window.action('3'); self.window.action('=')
            assert self.window.engine.number() == 3
            print(json.dumps({'gui':'PASS', 'standard':20, 'scientific':14, 'hex_and':3,
                'gtk':f'{Gtk.get_major_version()}.{Gtk.get_minor_version()}',
                'display':Gdk.Display.get_default().get_name()}), flush=True)
        except Exception:
            import traceback; traceback.print_exc(); self.smoke_failed = True
        self.quit()
        return False


if __name__ == '__main__':
    app = App()
    result = app.run([sys.argv[0]])
    sys.exit(1 if getattr(app,'smoke_failed',False) else result)
