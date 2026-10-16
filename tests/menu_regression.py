"""Exercise popup surfaces and pointer input across calculator layout changes."""
import json
import os
import subprocess
import sys
from pathlib import Path

if os.environ.get('CALC_XP_TEST_INSTALLED') == '1':
    sys.path.insert(0, '/usr/share/calc-xp')
    from app import App, Gtk, GLib
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from calc_xp.app import App, Gtk, GLib

POINTER = '--pointer' in sys.argv
if POINTER:
    import gi
    gi.require_version('GdkX11','4.0')
    from gi.repository import GdkX11, Graphene


def click(widget):
    if not POINTER:
        if isinstance(widget, Gtk.MenuButton): widget.popup()
        else: widget.emit('clicked')
        return
    native = widget.get_native()
    point = Graphene.Point()
    point.init(widget.get_width()/2, widget.get_height()/2)
    ok, position = widget.compute_point(native, point)
    assert ok, 'Could not locate the clickable widget'
    xid = native.get_surface().get_xid()
    if isinstance(widget, Gtk.MenuButton):
        subprocess.run(['xdotool','windowactivate','--sync',str(xid)],check=True,timeout=3)
    subprocess.run(['xdotool','mousemove','--sync','--window',str(xid),
        str(round(position.x)),str(round(position.y)),'click','1'],check=True)


app = App()
results = []
failed = []
loop = GLib.MainLoop()


def later(callback, delay=250):
    def run():
        try:
            callback()
        except Exception as exc:
            failed.append(str(exc))
            import traceback
            traceback.print_exc()
            loop.quit()
        return False
    GLib.timeout_add(delay, run)


def menu(label):
    child = app.window.root.get_first_child().get_first_child()
    while child:
        if child.get_label() == label:
            return child
        child = child.get_next_sibling()
    raise AssertionError(label)


def item(menu_button, label):
    child = menu_button.get_popover().get_child().get_first_child()
    while child:
        if child.get_label() == label:
            return child
        child = child.get_next_sibling()
    raise AssertionError(label)


def cycle(index=0):
    if index == 8:
        print(json.dumps({'menu_regression':'PASS','pointer_events':POINTER,
            'installed':os.environ.get('CALC_XP_TEST_INSTALLED') == '1','cycles':results}), flush=True)
        app.window.destroy()
        loop.quit()
        return
    view = menu('Exibir')
    click(view)
    later(lambda: select(index, view))


def select(index, view):
    assert view.get_active(), 'Exibir did not activate'
    assert view.get_popover().get_mapped(), 'Exibir did not map'
    target = 'scientific' if index % 2 == 0 else 'standard'
    click(item(view, 'Científica' if target == 'scientific' else 'Padrão'))
    later(lambda: check_closed(index, target, view))


def check_closed(index, target, view):
    assert not view.get_active(), 'Exibir remained active after selection'
    assert not view.get_popover().get_mapped(), 'Exibir popup remained mapped after selection'
    assert app.window.engine.mode == target, 'Mode was not changed'
    edit = menu('Editar')
    click(edit)
    later(lambda: check_edit(index, target, edit))


def check_edit(index, target, edit):
    assert edit.get_active(), 'Editar did not activate after switching modes'
    assert edit.get_popover().get_mapped(), 'Editar did not reopen after switching modes'
    click(item(edit, 'Copiar        Ctrl+C'))
    later(lambda: check_edit_closed(index, target, edit))


def check_edit_closed(index, target, edit):
    assert not edit.get_active(), 'Editar remained active'
    assert not edit.get_popover().get_mapped(), 'Editar remained mapped'
    for key in ('clear','2','+','3','='):
        app.window.action(key)
    assert app.window.engine.number() == 5
    results.append({'mode':target,'menus_reopened':True,'calculator_responsive':True})
    cycle(index+1)


def timeout():
    failed.append('Menu regression timed out')
    loop.quit()
    return False


app.register(None)
app.activate()
original_rebuild = app.window.rebuild
def guarded_rebuild():
    for label in ('Editar', 'Exibir', 'Ajuda'):
        assert not menu(label).get_popover().get_mapped(), 'Layout resized before the popup closed: ' + label
    original_rebuild()
app.window.rebuild = guarded_rebuild
later(cycle, 700)
GLib.timeout_add_seconds(20, timeout)
loop.run()
sys.exit(1 if failed else 0)
