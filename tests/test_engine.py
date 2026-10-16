import json
from pathlib import Path
from decimal import Decimal
import unittest

from calc_xp.engine import Calculator


def enter(calc, *keys):
    for key in keys: calc.press(key)
    return None if calc.error else calc.number()


class CompatibilityTests(unittest.TestCase):
    def test_recorded_original_results(self):
        """Replay classic calculator behavior, including its contextual percent semantics."""
        fixtures = Path(__file__).resolve().parent / 'fixtures'
        names = ['standard.json', 'scientific.json']
        aliases = {'C':'clear', 'sqt':'sqrt', '1/x':'reciprocal', 'x^y':'pow', 'n!':'factorial', 'And':'and'}
        cases_checked = 0
        for name in names:
            calc = Calculator()
            if 'scientific' in name: calc.set_mode('scientific')
            cases = json.loads((fixtures / name).read_text(encoding='utf-8'))
            if isinstance(cases, dict): cases = [cases]
            for case in cases:
                with self.subTest(name=case['Name']):
                    for key in case['keys']:
                        if key in ('Hex','Dec','Oct','Bin'):
                            calc.change_base({'Hex':16,'Dec':10,'Oct':8,'Bin':2}[key])
                        else: calc.press(aliases.get(key,key))
                    expected = case['result']
                    if 'zero' in expected:
                        self.assertIsNotNone(calc.error)
                    elif calc.base != 10:
                        self.assertEqual(calc.entry, expected)
                    else:
                        self.assertIsNone(calc.error)
                        self.assertEqual(calc.number(), Decimal(expected.replace(',','.').rstrip('.')))
                    cases_checked += 1
        self.assertEqual(cases_checked, 17)


class CalculatorTests(unittest.TestCase):
    def setUp(self): self.calc = Calculator()

    def test_decimal_precision(self):
        self.assertEqual(enter(self.calc,'0','.','1','+','0','.','2','='), Decimal('0.3'))

    def test_nested_parentheses(self):
        self.calc.set_mode('scientific')
        self.assertEqual(enter(self.calc,'2','*','(','3','+','(','4','*','5',')',')','='),46)

    def test_replace_operator(self):
        self.assertEqual(enter(self.calc,'2','+','*','3','='),6)

    def test_function_then_operator(self):
        self.assertEqual(enter(self.calc,'2','+','9','sqrt','*','4','='),20)

    def test_inverse_functions(self):
        self.calc.inverse = True
        self.assertEqual(enter(self.calc,'9','square'),3)
        enter(self.calc,'clear','8','pow','3','=')
        self.assertAlmostEqual(self.calc.number(),Decimal(2),places=28)

    def test_new_number_cancels_repeat(self):
        enter(self.calc,'2','+','3','=')
        self.assertEqual(enter(self.calc,'7','='),7)

    def test_error_recovery(self):
        enter(self.calc,'9','sqrt')
        self.calc.press('clear'); self.calc.press('1'); self.calc.press('/'); self.calc.press('0'); self.calc.press('=')
        self.assertIsNotNone(self.calc.error)
        self.assertEqual(enter(self.calc,'7'),7)

    def test_domain_error(self):
        enter(self.calc,'9','+/-','sqrt')
        self.assertIsNotNone(self.calc.error)

    def test_reciprocal_zero(self):
        self.calc.press('reciprocal')
        self.assertIsNotNone(self.calc.error)

    def test_memory_survives_clear(self):
        self.assertEqual(enter(self.calc,'4','2','MS','clear','MR'),42)
        enter(self.calc,'clear','8','M+','clear','MR')
        self.assertEqual(self.calc.number(),50)
        self.calc.press('MC'); self.assertEqual(self.calc.memory,0)

    def test_base_conversion(self):
        enter(self.calc,'2','5','5'); self.calc.change_base(16)
        self.assertEqual(self.calc.entry,'FF')
        self.calc.change_base(2); self.assertEqual(self.calc.entry,'11111111')
        self.calc.change_base(8); self.assertEqual(self.calc.entry,'377')
        self.calc.change_base(10); self.assertEqual(self.calc.number(),255)

    def test_invalid_binary_digit(self):
        self.calc.change_base(2)
        enter(self.calc,'1','2','0'); self.assertEqual(self.calc.entry,'10')

    def test_word_not(self):
        self.calc.bits = 8; self.calc.change_base(16)
        self.assertEqual(enter(self.calc,'0','not'),255)
        self.assertEqual(self.calc.entry,'FF')

    def test_shift(self):
        self.assertEqual(enter(self.calc,'1','lsh','3','='),8)
        self.calc.clear(); self.calc.inverse=True
        self.assertEqual(enter(self.calc,'8','lsh','2','='),2)

    def test_shift_guard(self):
        enter(self.calc,'1','lsh','9','9','9','=')
        self.assertIsNotNone(self.calc.error)

    def test_stats(self):
        for key in ('1','Dat','clear','2','Dat','clear','3','Dat'): self.calc.press(key)
        self.calc.press('average'); self.assertEqual(self.calc.number(),2)
        self.calc.press('stddev'); self.assertEqual(self.calc.number(),1)
        self.calc.press('sum'); self.assertEqual(self.calc.number(),6)
        self.calc.inverse=True; self.calc.press('sum'); self.assertEqual(self.calc.number(),14)

    def test_factorial_guard(self):
        enter(self.calc,'1','.','5','factorial'); self.assertIsNotNone(self.calc.error)

    def test_trig_angles(self):
        self.assertEqual(enter(self.calc,'3','0','sin'),Decimal('0.5'))
        self.calc.clear(); self.calc.angle='rad'
        self.calc.paste('1.5707963267948966'); self.calc.press('sin')
        self.assertEqual(self.calc.number(),1)

    def test_inverse_trig(self):
        self.calc.paste('0.5'); self.calc.inverse=True; self.calc.press('sin')
        self.assertAlmostEqual(self.calc.number(),Decimal(30),places=12)

    def test_hyperbolic(self):
        self.calc.hyperbolic=True; self.calc.press('cos'); self.assertEqual(self.calc.number(),1)

    def test_dms_roundtrip(self):
        self.calc.paste('12.5'); self.calc.press('dms'); self.assertEqual(self.calc.number(),Decimal('12.3'))
        self.calc.inverse=True; self.calc.press('dms'); self.assertEqual(self.calc.number(),Decimal('12.5'))

    def test_exponent_input(self):
        self.assertEqual(enter(self.calc,'2','Exp','+/-','3'),Decimal('0.002'))

    def test_backspace(self):
        self.assertEqual(enter(self.calc,'1','2','3','Backspace'),12)

    def test_display_grouping(self):
        self.calc.put(Decimal('12345.67'))
        self.assertEqual(self.calc.display(True),'12.345,67')
        self.assertEqual(self.calc.display(True,'.'),'12,345.67')
        self.calc.put(12345); self.assertEqual(self.calc.display(True),'12.345,')

    def test_numeric_paste(self):
        self.calc.paste('-12,5e2'); self.assertEqual(self.calc.number(),-1250)
        with self.assertRaises(ValueError): self.calc.paste('__import__("os").system("id")')


if __name__ == '__main__': unittest.main(verbosity=2)
